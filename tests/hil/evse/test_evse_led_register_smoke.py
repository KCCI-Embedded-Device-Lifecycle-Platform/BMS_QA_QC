from __future__ import annotations
import os, re, shutil, subprocess

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
    speed = os.getenv("OPENOCD_ADAPTER_KHZ", "1000").strip()
    serial = os.getenv("EVSE_STLINK_SERIAL", "").strip()
    cmd = ["openocd", "-f", board_cfg]
    if serial:
        cmd += ["-c", f"adapter serial {serial}"]
    cmd += ["-c", f"adapter speed {speed}"]
    return cmd

def _print_usb_diagnostics() -> None:
    print("=== HIL USB diagnostics ===")
    if shutil.which("lsusb"):
        r = subprocess.run(["lsusb"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, check=False)
        print(r.stdout)

def _cleanup_target() -> None:
    cmd = _openocd_base_command() + ["-c", "init; reset run; shutdown"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=15, check=False)

def _append_readback(lines: list[str], marker: str) -> None:
    lines += [
        f"set qa_odr [lindex [read_memory 0x{GPIOB_ODR:08X} 32 1] 0]",
        f'echo "QA_ODR_{marker}=$qa_odr"',
    ]

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
    ]
    _append_readback(lines, "OFF_INITIAL")
    lines.append("sleep 500")

    for n in range(1, 4):
        lines += [f'echo "QA_LD1_ON_{n}"',
                  f"mww 0x{GPIOB_BSRR:08X} 0x{LD1_MASK:08X}"]
        _append_readback(lines, f"ON_{n}")
        lines.append("sleep 1000")

        lines += [f'echo "QA_LD1_OFF_{n}"',
                  f"mww 0x{GPIOB_BSRR:08X} 0x{LD1_RESET_MASK:08X}"]
        _append_readback(lines, f"OFF_{n}")
        lines.append("sleep 1000")

    lines += ['echo "QA_EVSE_LD1_TEST_END"', "reset run", "shutdown"]
    return "\n".join(lines)

def test_evse_onboard_ld1_smoke() -> None:
    if shutil.which("openocd") is None:
        raise AssertionError("openocd is not installed on HIL-PI.")

    _print_usb_diagnostics()
    cmd = _openocd_base_command() + ["-c", _ld1_test_script()]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=45, check=False)
    except subprocess.TimeoutExpired as exc:
        _cleanup_target()
        raise AssertionError(f"OpenOCD timeout after {exc.timeout} seconds") from exc

    print(result.stdout)

    if result.returncode != 0:
        _cleanup_target()
        raise AssertionError(
            "OpenOCD failed.\n"
            f"returncode={result.returncode}\n"
            f"{result.stdout}"
        )

    assert "QA_EVSE_LD1_TEST_BEGIN" in result.stdout
    assert "QA_EVSE_LD1_TEST_END" in result.stdout

    matches = re.findall(r"QA_ODR_([A-Z0-9_]+)=([0-9A-Fa-fx]+)", result.stdout)
    parsed = {name: int(value, 0) & LD1_MASK for name, value in matches}

    expected = {
        "OFF_INITIAL": 0,
        "ON_1": 1,
        "OFF_1": 0,
        "ON_2": 1,
        "OFF_2": 0,
        "ON_3": 1,
        "OFF_3": 0,
    }

    missing = [k for k in expected if k not in parsed]
    assert not missing, f"Missing ODR markers: {missing}; captured={parsed}"

    mismatches = {
        k: {"expected": expected[k], "actual": parsed[k]}
        for k in expected if parsed[k] != expected[k]
    }
    assert not mismatches, f"ODR mismatch: {mismatches}; captured={parsed}"

    print("ODR_RESULT=" + ",".join(f"{k}:{parsed[k]}" for k in expected))
    print("RESULT=PASS TC-EVSE-LD1-001")