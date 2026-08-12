from __future__ import annotations

import os
import re
import shutil
import subprocess


# ---------------------------------------------------------------------------
# TC-EVSE-REL-001 / BEOG-17
#
# EVSE Application is linked at 0x08020000, while reset starts from the
# boot/OTA image at 0x08000000.  Therefore this application-level HIL smoke
# deliberately launches the EVSE application vector directly.
#
# This test verifies:
#   - valid application vector
#   - application actually runs from 0x0802xxxx
#   - VTOR points to the EVSE application vector
#   - GPIOE clock enabled
#   - RELAY_CTRL PE11 = Output / Push-Pull / Low Speed / No Pull
#   - RELAY_CTRL PE11 = LOW (Safe-Off)
#
# This test does NOT verify CAN->relay timing or the physical contactor.
# ---------------------------------------------------------------------------

APP_BASE = 0x08020000
APP_END = 0x08200000  # STM32F429 2 MiB flash end

SRAM_BASE = 0x20000000
SRAM_END = 0x20030000  # 192 KiB SRAM; initial MSP may equal SRAM_END

SCB_VTOR = 0xE000ED08
SCB_CFSR = 0xE000ED28
SCB_HFSR = 0xE000ED2C

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
    # Accept OpenOCD/Tcl decimal or hexadecimal marker values.
    match = re.search(
        rf"{re.escape(name)}=(0x[0-9A-Fa-f]+|[0-9]+)",
        output,
    )
    assert match, f"{name} not found in OpenOCD output"
    return int(match.group(1), 0)


def _last_halted_pc(output: str) -> int:
    # OpenOCD halt line example:
    # xPSR: 0x01000000 pc: 0x080250de psp: ...
    pcs = re.findall(r"\bpc:\s*(0x[0-9A-Fa-f]+)", output)
    assert pcs, "No halted PC found in OpenOCD output"
    return int(pcs[-1], 16)


def test_evse_relay_pe11_safe_off_smoke() -> None:
    """TC-EVSE-REL-001 / BEOG-17 / application-level HIL smoke."""

    assert shutil.which("openocd"), "openocd is not installed on HIL-PI"

    script = f"""
init
reset halt

echo "QA_EVSE_RELAY_PE11_BEGIN"

set app_sp [lindex [read_memory 0x{APP_BASE:08X} 32 1] 0]
set app_pc [lindex [read_memory 0x{APP_BASE + 4:08X} 32 1] 0]
set app_entry [expr {{$app_pc & 0xFFFFFFFE}}]

echo "QA_APP_SP=$app_sp"
echo "QA_APP_PC=$app_pc"
echo "QA_APP_ENTRY=$app_entry"

# Direct-launch the EVSE Application.
# Reset normally enters the boot/OTA image at 0x08000000; BEOG-17 is scoped
# to the EVSE application, not bootloader hand-off verification.
mww 0x{SCB_VTOR:08X} 0x{APP_BASE:08X}
reg msp $app_sp
reg pc $app_entry
reg xpsr 0x01000000

resume
sleep 1000
halt

echo "QA_APP_RUNNING"

set qa_vtor [lindex [read_memory 0x{SCB_VTOR:08X} 32 1] 0]
set qa_rcc [lindex [read_memory 0x{RCC_AHB1ENR:08X} 32 1] 0]
set qa_moder [lindex [read_memory 0x{GPIOE_MODER:08X} 32 1] 0]
set qa_otyper [lindex [read_memory 0x{GPIOE_OTYPER:08X} 32 1] 0]
set qa_ospeedr [lindex [read_memory 0x{GPIOE_OSPEEDR:08X} 32 1] 0]
set qa_pupdr [lindex [read_memory 0x{GPIOE_PUPDR:08X} 32 1] 0]
set qa_odr [lindex [read_memory 0x{GPIOE_ODR:08X} 32 1] 0]
set qa_cfsr [lindex [read_memory 0x{SCB_CFSR:08X} 32 1] 0]
set qa_hfsr [lindex [read_memory 0x{SCB_HFSR:08X} 32 1] 0]

echo "QA_VTOR=$qa_vtor"
echo "QA_RCC_AHB1ENR=$qa_rcc"
echo "QA_GPIOE_MODER=$qa_moder"
echo "QA_GPIOE_OTYPER=$qa_otyper"
echo "QA_GPIOE_OSPEEDR=$qa_ospeedr"
echo "QA_GPIOE_PUPDR=$qa_pupdr"
echo "QA_GPIOE_ODR=$qa_odr"
echo "QA_CFSR=$qa_cfsr"
echo "QA_HFSR=$qa_hfsr"

echo "QA_EVSE_RELAY_PE11_END"

# Leave the EVSE application running after observation.
resume
shutdown
"""

    result = subprocess.run(
        _openocd_base() + ["-c", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=35,
        check=False,
    )

    print(result.stdout)

    assert result.returncode == 0, result.stdout
    assert "QA_EVSE_RELAY_PE11_BEGIN" in result.stdout
    assert "QA_APP_RUNNING" in result.stdout
    assert "QA_EVSE_RELAY_PE11_END" in result.stdout

    app_sp = _read_marker(result.stdout, "QA_APP_SP")
    app_pc = _read_marker(result.stdout, "QA_APP_PC")
    app_entry = _read_marker(result.stdout, "QA_APP_ENTRY")

    # Application vector sanity.
    assert SRAM_BASE <= app_sp <= SRAM_END, (
        f"Invalid EVSE APP initial MSP: 0x{app_sp:08X}"
    )
    assert app_pc & 0x1, (
        f"EVSE APP reset vector is not Thumb: 0x{app_pc:08X}"
    )
    assert APP_BASE <= app_entry < APP_END, (
        f"EVSE APP entry outside application flash: 0x{app_entry:08X}"
    )

    # After one second, CPU should still execute inside the EVSE app flash.
    running_pc = _last_halted_pc(result.stdout)
    assert APP_BASE <= running_pc < APP_END, (
        "CPU is not executing the EVSE application after direct launch: "
        f"PC=0x{running_pc:08X}"
    )

    vtor = _read_marker(result.stdout, "QA_VTOR")
    rcc = _read_marker(result.stdout, "QA_RCC_AHB1ENR")
    moder = _read_marker(result.stdout, "QA_GPIOE_MODER")
    otyper = _read_marker(result.stdout, "QA_GPIOE_OTYPER")
    ospeedr = _read_marker(result.stdout, "QA_GPIOE_OSPEEDR")
    pupdr = _read_marker(result.stdout, "QA_GPIOE_PUPDR")
    odr = _read_marker(result.stdout, "QA_GPIOE_ODR")

    # The test harness deliberately points VTOR to the application vector.
    assert vtor == APP_BASE, (
        f"VTOR mismatch: expected 0x{APP_BASE:08X}, actual 0x{vtor:08X}"
    )

    # GPIOE peripheral clock enabled.
    assert rcc & GPIOE_CLOCK_MASK, (
        f"GPIOE clock disabled: RCC_AHB1ENR=0x{rcc:08X}"
    )

    # PE11 MODER = 01: general-purpose output.
    assert (moder & PE11_2BIT_MASK) == PE11_MODE_OUTPUT, (
        f"PE11 is not output mode: MODER=0x{moder:08X}"
    )

    # Push-pull.
    assert (otyper & PE11_BIT) == 0, (
        f"PE11 is not push-pull: OTYPER=0x{otyper:08X}"
    )

    # Low speed = 00.
    assert (ospeedr & PE11_2BIT_MASK) == 0, (
        f"PE11 speed differs from product baseline: OSPEEDR=0x{ospeedr:08X}"
    )

    # No pull = 00.
    assert (pupdr & PE11_2BIT_MASK) == 0, (
        f"PE11 pull differs from product baseline: PUPDR=0x{pupdr:08X}"
    )

    # Safe-Off: PE11 LOW.
    assert (odr & PE11_BIT) == 0, (
        f"RELAY_CTRL PE11 is HIGH; expected Safe-Off LOW: ODR=0x{odr:08X}"
    )

    cfsr = _read_marker(result.stdout, "QA_CFSR")
    hfsr = _read_marker(result.stdout, "QA_HFSR")

    print(f"QA_APP_RUNNING_PC=0x{running_pc:08X}")
    print(f"QA_APP_ENTRY_HEX=0x{app_entry:08X}")
    print(f"QA_CFSR_HEX=0x{cfsr:08X}")
    print(f"QA_HFSR_HEX=0x{hfsr:08X}")
    print("RESULT=PASS TC-EVSE-REL-001")