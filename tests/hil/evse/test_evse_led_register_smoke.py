from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass


RCC_AHB1ENR = 0x40023830
GPIOB_MODER = 0x40020400
GPIOB_OTYPER = 0x40020404
GPIOB_OSPEEDR = 0x40020408
GPIOB_PUPDR = 0x4002040C
GPIOB_ODR = 0x40020414
GPIOB_BSRR = 0x40020418

LD1 = 1 << 0      # PB0
LD2 = 1 << 7      # PB7
LD3 = 1 << 14     # PB14
LED_MASK = LD1 | LD2 | LD3

GPIO_2BIT_FIELD_MASK = (0b11 << 0) | (0b11 << 14) | (0b11 << 28)
GPIO_OUTPUT_MODE_BITS = (0b01 << 0) | (0b01 << 14) | (0b01 << 28)


@dataclass(frozen=True)
class LedStep:
    marker: str
    set_mask: int
    expected_mask: int
    hold_ms: int


LED_STEPS = (
    LedStep("QA_ALL_LEDS_OFF_INITIAL", 0, 0, 300),
    LedStep("QA_LD1_ON", LD1, LD1, 1000),
    LedStep("QA_ALL_LEDS_OFF_AFTER_LD1", 0, 0, 300),
    LedStep("QA_LD2_ON", LD2, LD2, 1000),
    LedStep("QA_ALL_LEDS_OFF_AFTER_LD2", 0, 0, 300),
    LedStep("QA_LD3_ON", LD3, LD3, 1000),
    LedStep("QA_ALL_LEDS_OFF_AFTER_LD3", 0, 0, 300),
    LedStep("QA_ALL_LEDS_ON", LED_MASK, LED_MASK, 1000),
    LedStep("QA_ALL_LEDS_OFF_FINAL", 0, 0, 300),
)


def _hex32(value: int) -> str:
    return f"0x{value & 0xFFFFFFFF:08X}"


def _openocd_base_command() -> list[str]:
    interface_cfg = os.getenv(
        "OPENOCD_INTERFACE_CFG",
        "interface/stlink.cfg",
    )
    target_cfg = os.getenv(
        "OPENOCD_TARGET_CFG",
        "target/stm32f4x.cfg",
    )
    stlink_serial = os.getenv("EVSE_STLINK_SERIAL", "").strip()

    command = [
        "openocd",
        "-f",
        interface_cfg,
        "-f",
        target_cfg,
    ]

    if stlink_serial:
        command.extend(["-c", f"adapter serial {stlink_serial}"])

    return command


def _configuration_script() -> str:
    clear_2bit_mask = (~GPIO_2BIT_FIELD_MASK) & 0xFFFFFFFF
    clear_1bit_mask = (~LED_MASK) & 0xFFFFFFFF

    lines = [
        "init",
        "reset halt",
        'echo "QA_EVSE_LED_TEST_BEGIN"',
        f"set rcc [lindex [read_memory {_hex32(RCC_AHB1ENR)} 32 1] 0]",
        (
            f"write_memory {_hex32(RCC_AHB1ENR)} 32 "
            f"[list [expr {{$rcc | 0x00000002}}]]"
        ),
        f"set moder [lindex [read_memory {_hex32(GPIOB_MODER)} 32 1] 0]",
        (
            f"write_memory {_hex32(GPIOB_MODER)} 32 "
            f"[list [expr {{($moder & {_hex32(clear_2bit_mask)}) | "
            f"{_hex32(GPIO_OUTPUT_MODE_BITS)}}}]]"
        ),
        f"set otyper [lindex [read_memory {_hex32(GPIOB_OTYPER)} 32 1] 0]",
        (
            f"write_memory {_hex32(GPIOB_OTYPER)} 32 "
            f"[list [expr {{$otyper & {_hex32(clear_1bit_mask)}}}]]"
        ),
        f"set ospeedr [lindex [read_memory {_hex32(GPIOB_OSPEEDR)} 32 1] 0]",
        (
            f"write_memory {_hex32(GPIOB_OSPEEDR)} 32 "
            f"[list [expr {{$ospeedr & {_hex32(clear_2bit_mask)}}}]]"
        ),
        f"set pupdr [lindex [read_memory {_hex32(GPIOB_PUPDR)} 32 1] 0]",
        (
            f"write_memory {_hex32(GPIOB_PUPDR)} 32 "
            f"[list [expr {{$pupdr & {_hex32(clear_2bit_mask)}}}]]"
        ),
    ]

    reset_mask = LED_MASK << 16

    for step in LED_STEPS:
        lines.append(f'echo "{step.marker}"')
        lines.append(f"mww {_hex32(GPIOB_BSRR)} {_hex32(reset_mask)}")
        if step.set_mask != 0:
            lines.append(
                f"mww {_hex32(GPIOB_BSRR)} {_hex32(step.set_mask)}"
            )
        lines.append(f"mdw {_hex32(GPIOB_ODR)} 1")
        lines.append(f"sleep {step.hold_ms}")

    lines.extend(
        [
            'echo "QA_EVSE_LED_TEST_END"',
            "reset run",
            "shutdown",
        ]
    )
    return "\n".join(lines)


def _cleanup_target() -> None:
    cleanup_command = _openocd_base_command()
    cleanup_command.extend(["-c", "init; reset run; shutdown"])
    subprocess.run(
        cleanup_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=15,
        check=False,
    )


def test_evse_onboard_led_register_smoke() -> None:
    command = _openocd_base_command()
    command.extend(["-c", _configuration_script()])

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
            "OpenOCD execution failed\n"
            f"returncode={result.returncode}\n"
            f"{result.stdout}"
        )

    assert "QA_EVSE_LED_TEST_BEGIN" in result.stdout
    assert "QA_EVSE_LED_TEST_END" in result.stdout

    odr_values = [
        int(value, 16) & LED_MASK
        for value in re.findall(
            r"0x40020414:\s+([0-9a-fA-F]{8})",
            result.stdout,
        )
    ]

    expected_masks = [step.expected_mask for step in LED_STEPS]

    assert len(odr_values) >= len(expected_masks), (
        "Not enough GPIOB ODR readback values were captured.\n"
        f"expected_count={len(expected_masks)}\n"
        f"actual_values={odr_values}"
    )

    actual_tail = odr_values[-len(expected_masks):]

    assert actual_tail == expected_masks, (
        "GPIOB LED-bit readback sequence differs from the expected sequence.\n"
        f"expected={expected_masks}\n"
        f"actual={actual_tail}"
    )

    print("RESULT=PASS TC-EVSE-LED-001")
