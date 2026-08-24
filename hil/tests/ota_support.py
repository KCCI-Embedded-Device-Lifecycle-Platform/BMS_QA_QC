from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import pytest

from hil.boot_protocol_client import BootProtocolClient
from hil.openocd_client import OpenOcdClient
from hil.power_fault_controller import ExternalCommandController
from hil.uart_adapter import UartAdapter, UartConfig


def recovery_image(hil_config: dict[str, Any]) -> bytes:
    configured = os.getenv("OTA_RECOVERY_IMAGE") or hil_config.get("ota", {}).get(
        "recovery_image"
    )
    if not configured:
        pytest.skip("BLOCKED_INFRA: OTA_RECOVERY_IMAGE/recovery_image is not configured")
    path = Path(str(configured))
    if not path.is_file():
        pytest.fail(f"BLOCKED_INFRA: recovery image does not exist: {path}")
    image = path.read_bytes()
    if not 8 <= len(image) <= 0xE0000:
        pytest.fail(f"MISMATCH_CONFIGURATION: recovery image size={len(image)}")
    return image


def enter_bootloader(hil_config: dict[str, Any]) -> None:
    if os.getenv("HIL_ALLOW_RESET") != "YES":
        pytest.skip("BLOCKED_INFRA: HIL_ALLOW_RESET=YES is required")
    stimulus = hil_config.get("stimulus", {})
    press = str(stimulus.get("boot_button_press_command", ""))
    release = str(stimulus.get("boot_button_release_command", ""))
    if not press or not release:
        pytest.skip("BLOCKED_INFRA: boot button press/release controls are not configured")
    config = hil_config.get("openocd", {}).get(
        "ota", hil_config.get("openocd", {}).get("evse", {})
    )
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


def open_binary_client(hil_config: dict[str, Any]) -> tuple[UartAdapter, BootProtocolClient]:
    uart = hil_config.get("uart", {})
    adapter = UartAdapter(
        UartConfig(
            port=str(uart.get("port", "/dev/ttyUSB1")),
            baudrate=int(uart.get("baudrate", 115200)),
            timeout_s=float(uart.get("timeout_s", 2.0)),
        )
    )
    adapter.reset_input_buffer()
    adapter.write(b"PROTO\r\n")
    response = adapter.read_until(b"\n")
    if response != b"[BOOT] Enter binary protocol mode\r\n":
        adapter.close()
        raise AssertionError(f"boot PROTO response mismatch: {response!r}")
    return adapter, BootProtocolClient(adapter)
