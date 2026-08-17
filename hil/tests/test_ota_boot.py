from __future__ import annotations

import os
import time
from typing import Any

import pytest

from hil.openocd_client import OpenOcdClient
from hil.power_fault_controller import ExternalCommandController
from hil.uart_adapter import UartAdapter, UartConfig

APP_START = 0x08020000
APP_END = 0x08100000


def _uart_config(hil_config: dict[str, Any]) -> UartConfig:
    uart = hil_config.get("uart", {})
    return UartConfig(
        port=str(uart.get("port", "/dev/ttyUSB1")),
        baudrate=int(uart.get("baudrate", 115200)),
        timeout_s=float(uart.get("timeout_s", 1.0)),
    )


@pytest.mark.hil
@pytest.mark.destructive
def test_tc_ota_boot_001_valid_app_is_entered(hil_config: dict[str, Any]) -> None:
    """TC-OTA-BOOT-001: a valid image transfers execution into the app range."""

    if os.getenv("HIL_ALLOW_RESET") != "YES":
        pytest.skip("BLOCKED_INFRA: HIL_ALLOW_RESET=YES is required")
    config = hil_config.get("openocd", {}).get("ota", hil_config.get("openocd", {}).get("evse", {}))
    with OpenOcdClient(
        host=str(config.get("host", "127.0.0.1")),
        port=int(config.get("port", 4444)),
    ) as client:
        client.command("reset run")
        time.sleep(0.5)
        client.command("halt")
        pc = client.read_register("pc")
        assert APP_START <= pc < APP_END, (
            f"PC 0x{pc:08X} is outside application region"
        )
        client.command("resume")


@pytest.mark.hil
@pytest.mark.destructive
def test_tc_ota_boot_002_button_holds_bootloader(hil_config: dict[str, Any]) -> None:
    """TC-OTA-BOOT-002: user-button request prevents auto-jump and serves HELLO."""

    if os.getenv("HIL_ALLOW_RESET") != "YES":
        pytest.skip("BLOCKED_INFRA: HIL_ALLOW_RESET=YES is required")
    stimulus = hil_config.get("stimulus", {})
    press = str(stimulus.get("boot_button_press_command", ""))
    release = str(stimulus.get("boot_button_release_command", ""))
    if not press or not release:
        pytest.skip("BLOCKED_INFRA: boot button press/release controls are not configured")
    config = hil_config.get("openocd", {}).get("ota", hil_config.get("openocd", {}).get("evse", {}))

    ExternalCommandController(press, "HIL_ALLOW_BOOT_CONTROL").trigger()
    try:
        with OpenOcdClient(
            host=str(config.get("host", "127.0.0.1")),
            port=int(config.get("port", 4444)),
        ) as client:
            client.command("reset run")
        time.sleep(0.3)
    finally:
        ExternalCommandController(release, "HIL_ALLOW_BOOT_CONTROL").trigger()

    with UartAdapter(_uart_config(hil_config)) as uart:
        uart.reset_input_buffer()
        uart.write(b"HELLO\r\n")
        response = uart.read_until(b"\n")
    assert response == b"[BOOT] ACK\r\n"
