from __future__ import annotations

import os
import re
import shutil
import subprocess


# STM32F429 GPIOE registers
RCC_AHB1ENR = 0x40023830
GPIOE_MODER = 0x40021000
GPIOE_OTYPER = 0x40021004
GPIOE_OSPEEDR = 0x40021008
GPIOE_PUPDR = 0x4002100C
GPIOE_ODR = 0x40021014

GPIOE_CLOCK_MASK = 1 << 4

PE11 = 11
PE11_BIT = 1 << PE11
PE11_2BIT_SHIFT = PE11 * 2
PE11_2BIT_MASK = 0x3 << PE11_2BIT_SHIFT
PE11_MODE_OUTPUT = 0x1 << PE11_2BIT_SHIFT


def _openocd_base() -> list[str]:
    return [
        "openocd",
        "-f",
        os.getenv("OPENOCD_BOARD_CFG", "board/st_nucleo_f4.cfg"),
        "-c",
        f"adapter speed {os.getenv('OPENOCD_ADAPTER_KHZ', '1000')}",
    ]


def _read_marker(output: str, name: str) -> int:
    match = re.search(
        rf"{re.escape(name)}=([0-9A-Fa-fx]+)",
        output,
    )
    assert match, f"{name} not found in OpenOCD output"
    return int(match.group(1), 0)


def test_evse_relay_pe11_safe_off_smoke() -> None:
    """TC-EVSE-REL-001 / BEOG-17.

    Verifies the currently-flashed EVSE bench-safe firmware configures
    RELAY_CTRL(PE11) as output and keeps it LOW (Safe-Off).

    This is NOT the CAN->relay timing test.
    """

    assert shutil.which("openocd"), "openocd is not installed on HIL-PI"

    script = f"""
init
reset run
sleep 1000
halt

echo "QA_EVSE_RELAY_PE11_BEGIN"

set qa_rcc [lindex [read_memory 0x{RCC_AHB1ENR:08X} 32 1] 0]
set qa_moder [lindex [read_memory 0x{GPIOE_MODER:08X} 32 1] 0]
set qa_otyper [lindex [read_memory 0x{GPIOE_OTYPER:08X} 32 1] 0]
set qa_ospeedr [lindex [read_memory 0x{GPIOE_OSPEEDR:08X} 32 1] 0]
set qa_pupdr [lindex [read_memory 0x{GPIOE_PUPDR:08X} 32 1] 0]
set qa_odr [lindex [read_memory 0x{GPIOE_ODR:08X} 32 1] 0]

echo "QA_RCC_AHB1ENR=$qa_rcc"
echo "QA_GPIOE_MODER=$qa_moder"
echo "QA_GPIOE_OTYPER=$qa_otyper"
echo "QA_GPIOE_OSPEEDR=$qa_ospeedr"
echo "QA_GPIOE_PUPDR=$qa_pupdr"
echo "QA_GPIOE_ODR=$qa_odr"

echo "QA_EVSE_RELAY_PE11_END"

reset run
shutdown
"""

    result = subprocess.run(
        _openocd_base() + ["-c", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
        check=False,
    )

    print(result.stdout)
    assert result.returncode == 0, result.stdout

    assert "QA_EVSE_RELAY_PE11_BEGIN" in result.stdout
    assert "QA_EVSE_RELAY_PE11_END" in result.stdout

    rcc = _read_marker(result.stdout, "QA_RCC_AHB1ENR")
    moder = _read_marker(result.stdout, "QA_GPIOE_MODER")
    otyper = _read_marker(result.stdout, "QA_GPIOE_OTYPER")
    ospeedr = _read_marker(result.stdout, "QA_GPIOE_OSPEEDR")
    pupdr = _read_marker(result.stdout, "QA_GPIOE_PUPDR")
    odr = _read_marker(result.stdout, "QA_GPIOE_ODR")

    # GPIOE peripheral clock enabled.
    assert rcc & GPIOE_CLOCK_MASK, (
        f"GPIOE clock disabled: RCC_AHB1ENR=0x{rcc:08X}"
    )

    # PE11 MODER = 01: general purpose output.
    assert (moder & PE11_2BIT_MASK) == PE11_MODE_OUTPUT, (
        f"PE11 is not output mode: MODER=0x{moder:08X}"
    )

    # Push-pull.
    assert (otyper & PE11_BIT) == 0, (
        f"PE11 is not push-pull: OTYPER=0x{otyper:08X}"
    )

    # Low speed = 00.
    assert (ospeedr & PE11_2BIT_MASK) == 0, (
        f"PE11 speed differs from baseline: OSPEEDR=0x{ospeedr:08X}"
    )

    # No pull = 00.
    assert (pupdr & PE11_2BIT_MASK) == 0, (
        f"PE11 pull differs from baseline: PUPDR=0x{pupdr:08X}"
    )

    # Bench-safe relay output must remain LOW.
    assert (odr & PE11_BIT) == 0, (
        f"RELAY_CTRL PE11 is HIGH; expected Safe-Off LOW: ODR=0x{odr:08X}"
    )

    print("RESULT=PASS TC-EVSE-REL-001")
