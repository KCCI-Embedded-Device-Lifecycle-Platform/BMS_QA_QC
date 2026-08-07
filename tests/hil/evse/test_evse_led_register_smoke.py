from __future__ import annotations

import os
import re
import shutil
import subprocess

RCC_AHB1ENR = 0x40023830
GPIOB_MODER = 0x40020400
GPIOB_OTYPER = 0x40020404
GPIOB_OSPEEDR = 0x40020408
GPIOB_PUPDR = 0x4002040C
GPIOB_ODR = 0x40020414
GPIOB_BSRR = 0x40020418

LD1_MASK = 1 << 0
LD1_RESET_MASK = 1 << 16


def _openocd_base_command() -> list[str]:
    board_cfg = os.getenv("OPENOCD_BOARD_CFG", "board/st_nucleo_f4.cfg")
    adapter_speed = os.getenv("OPENOCD_ADAPTER_KHZ", "1000").strip()
    stlink_serial = os.getenv("EVSE_STLINK_SERIAL", "").strip()

    command = ["openocd", "-f", board_cfg]

    if stlink_serial:
        command.extend(["-c", f"adapter serial {stlink_serial}"])

    command.extend(["-c", f"adapter speed {adapter_speed}"])
    return command


def _print_usb_diagnostics() -> None:
    print("=== HIL USB diagnostics ===")

    if shutil.which("lsusb") is None:
        print("lsusb not installed; install package 'usbutils' on HIL-PI.")
        return

    result = subprocess.run(
        ["lsusb"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    print(result.stdout)

    if "0483:" not in result.stdout.lower():
        print(
            "WARNING: STMicroelectronics USB device (VID 0483) was not found. "
            "Check NUCLEO ST-LINK CN1, power, and USB enumeration."
        )


def _connection_error_message(output: str, returncode: int) -> str:
    return "\n".join(
        [
            "OpenOCD could not open/connect to the NUCLEO-F429ZI ST-LINK.",
            f"returncode={returncode}",
            "",
            "Check on HIL-PI:",
            "1) Connect NUCLEO CN1 (ST-LINK USB) directly to the Raspberry Pi.",
            "2) LD6 is only the PWR indicator; it should be ON when the target is powered.",
            "3) For on-board debug: CN4 both jumpers ON, JP3=U5V, JP5 ON, JP1 OFF.",
            "4) Close STM32CubeIDE, STM32CubeProgrammer, st-util, and other OpenOCD sessions.",
            "5) Run: lsusb | grep -i 0483",
            "6) Run: id gitlab-runner",
            "7) Direct test:",
            "   sudo -u gitlab-runner openocd -f board/st_nucleo_f4.cfg "
            "-c 'adapter speed 1000; init; reset halt; shutdown'",
            "",
            "OpenOCD output:",
            output,
        ]
    )


def _cleanup_target() -> None:
    command = _openocd_base_command()
    command.extend(["-c", "init; reset run; shutdown"])

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=15,
        check=False,
    )


def _ld1_test_script() -> str:
    lines = [
        "init",
        "reset halt",
        'echo "QA_EVSE_LD1_TEST_BEGIN"',
        f"mmw 0x{RCC_AHB1ENR:08X} 0x00000002 0x00000000",
        f"mmw 0x{GPIOB_MODER:08X} 0x00000001 0x00000003",
        f"mmw 0x{GPIOB_OTYPER:08X} 0x00000000 0x00000001",
        f"mmw 0x{GPIOB_OSPEEDR:08X} 0x00000000 0x00000003",
        f"mmw 0x{GPIOB_PUPDR:08X} 0x00000000 0x00000003",
        'echo "QA_LD1_OFF_INITIAL"',
        f"mww 0x{GPIOB_BSRR:08X} 0x{LD1_RESET_MASK:08X}",
        f"mdw 0x{GPIOB_ODR:08X} 1",
        "sleep 500",
    ]

    for cycle in range(1, 4):
        lines.extend(
            [
                f'echo "QA_LD1_ON_{cycle}"',
                f"mww 0x{GPIOB_BSRR:08X} 0x{LD1_MASK:08X}",
                f"mdw 0x{GPIOB_ODR:08X} 1",
                "sleep 1000",
                f'echo "QA_LD1_OFF_{cycle}"',
                f"mww 0x{GPIOB_BSRR:08X} 0x{LD1_RESET_MASK:08X}",
                f"mdw 0x{GPIOB_ODR:08X} 1",
                "sleep 1000",
            ]
        )

    lines.extend(
        [
            'echo "QA_EVSE_LD1_TEST_END"',
            "reset run",
            "shutdown",
        ]
    )
    return "\n".join(lines)


def test_evse_onboard_ld1_smoke() -> None:
    if shutil.which("openocd") is None:
        raise AssertionError(
            "openocd is not installed on HIL-PI."
        )

    _print_usb_diagnostics()

    command = _openocd_base_command()
    command.extend(["-c", _ld1_test_script()])

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=45,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        _cleanup_target()
        raise AssertionError(
            f"OpenOCD timeout after {exc.timeout} seconds"
        ) from exc

    print(result.stdout)

    if result.returncode != 0:
        _cleanup_target()
        raise AssertionError(
            _connection_error_message(result.stdout, result.returncode)
        )

    assert "QA_EVSE_LD1_TEST_BEGIN" in result.stdout
    assert "QA_EVSE_LD1_TEST_END" in result.stdout

    odr_values = [
        int(value, 16) & LD1_MASK
        for value in re.findall(
            r"0x40020414:\s+([0-9a-fA-F]{8})",
            result.stdout,
        )
    ]

    expected = [0, LD1_MASK, 0, LD1_MASK, 0, LD1_MASK, 0]

    assert len(odr_values) >= len(expected), (
        "Not enough GPIOB ODR readbacks were captured.\n"
        f"expected_count={len(expected)}\n"
        f"actual={odr_values}"
    )

    actual = odr_values[-len(expected):]

    assert actual == expected, (
        "PB0/LD1 register transition did not match the expected sequence.\n"
        f"expected={expected}\n"
        f"actual={actual}"
    )

    print("RESULT=PASS TC-EVSE-LD1-001")