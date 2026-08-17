from __future__ import annotations

import os
import time
from typing import Any

import pytest

from hil.openocd_client import OpenOcdClient

GPIOA_ODR = 0x40020014
GPIOE_ODR = 0x40021014
CFSR = 0xE000ED28
HFSR = 0xE000ED2C


def _reset_then_assert_low(
    config: dict[str, Any], address: int, mask: int, label: str, settle_s: float = 0.2
) -> None:
    with OpenOcdClient(
        host=str(config.get("host", "127.0.0.1")),
        port=int(config.get("port", 4444)),
    ) as client:
        client.command("reset run")
        time.sleep(settle_s)
        client.command("halt")
        odr = client.read_word(address)
        cfsr = client.read_word(CFSR)
        hfsr = client.read_word(HFSR)
        assert odr & mask == 0, f"{label} unsafe after reset: ODR=0x{odr:08X}"
        assert cfsr == 0, f"CFSR is non-zero after reset: 0x{cfsr:08X}"
        assert hfsr == 0, f"HFSR is non-zero after reset: 0x{hfsr:08X}"
        # The verdict is captured before execution resumes.
        client.command("resume")


@pytest.mark.hil
@pytest.mark.destructive
def test_tc_evse_safe_006_repeated_reset_starts_pe11_low(hil_config: dict[str, Any]) -> None:
    """TC-EVSE-SAFE-006: three arbitrary resets retain the safe relay state."""

    if os.getenv("HIL_ALLOW_RESET") != "YES":
        pytest.skip("BLOCKED_INFRA: HIL_ALLOW_RESET=YES is required")
    config = hil_config.get("openocd", {}).get("evse", {})
    for _ in range(3):
        _reset_then_assert_low(config, GPIOE_ODR, 1 << 11, "EVSE PE11")


@pytest.mark.hil
@pytest.mark.destructive
def test_tc_bms_relay_001_reset_starts_pa8_low(hil_config: dict[str, Any]) -> None:
    """TC-BMS-RELAY-001 prerequisite: BMS PA8 is open after reset."""

    if os.getenv("HIL_ALLOW_RESET") != "YES":
        pytest.skip("BLOCKED_INFRA: HIL_ALLOW_RESET=YES is required")
    config = hil_config.get("openocd", {}).get("bms", {})
    _reset_then_assert_low(config, GPIOA_ODR, 1 << 8, "BMS PA8")
