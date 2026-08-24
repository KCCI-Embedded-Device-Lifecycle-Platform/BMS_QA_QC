from __future__ import annotations

import time
from typing import Any

import pytest

from hil.can_adapter import CanAdapter, CanFrame
from hil.openocd_client import OpenOcdClient
from hil.power_fault_controller import ExternalCommandController


def _wait(adapter: CanAdapter, predicate, timeout_s: float) -> CanFrame:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        frame = adapter.recv(min(0.2, deadline - time.monotonic()))
        if frame is not None and predicate(frame):
            return frame
    raise AssertionError(f"required E2E transition not observed within {timeout_s:.2f}s")


def _read_odr(hil_config: dict[str, Any], target: str, address: int) -> int:
    config = hil_config.get("openocd", {}).get(target, {})
    with OpenOcdClient(
        host=str(config.get("host", "127.0.0.1")),
        port=int(config.get("port", 4444)),
    ) as client:
        return client.read_word(address)


@pytest.mark.hil
def test_tc_can_e2e_002_start_stop_state_sequence(
    can_adapter: CanAdapter, hil_config: dict[str, Any]
) -> None:
    """TC-CAN-E2E-002: START/STOP -> 0x201 -> BMS state and relay commands."""

    stimulus = hil_config.get("stimulus", {})
    start_command = str(stimulus.get("start_command", ""))
    stop_command = str(stimulus.get("stop_command", ""))
    if not start_command or not stop_command:
        pytest.skip("BLOCKED_INFRA: electrically isolated START/STOP controls are not configured")
    timeout_s = float(hil_config.get("timing", {}).get("e2e_timeout_s", 3.0))

    _wait(
        can_adapter,
        lambda f: f.arbitration_id == 0x200 and f.dlc == 4 and f.data[0] == 4,
        timeout_s,
    )
    ExternalCommandController(start_command, "HIL_ALLOW_ACTUATION").trigger()
    first_start = _wait(
        can_adapter,
        lambda f: f.arbitration_id == 0x201 and f.dlc == 1 and f.data[0] == 1,
        timeout_s,
    )
    bms_ready = _wait(
        can_adapter,
        lambda f: f.arbitration_id == 0x100
        and f.dlc == 8
        and f.data[5] == 1
        and f.data[6] in (3, 4),
        timeout_s,
    )
    evse_charging = _wait(
        can_adapter,
        lambda f: f.arbitration_id == 0x200
        and f.dlc == 4
        and f.data[0] == 5
        and f.data[1] == 1,
        timeout_s,
    )
    assert first_start.timestamp <= bms_ready.timestamp <= evse_charging.timestamp
    bms_gpioa = _read_odr(hil_config, "bms", 0x40020014)
    assert bms_gpioa & (1 << 8), f"BMS PA8 is LOW while charging: ODR=0x{bms_gpioa:08X}"

    ExternalCommandController(stop_command, "HIL_ALLOW_ACTUATION").trigger()
    first_stop = _wait(
        can_adapter,
        lambda f: f.arbitration_id == 0x201 and f.dlc == 1 and f.data[0] == 0,
        timeout_s,
    )
    evse_off = _wait(
        can_adapter,
        lambda f: f.arbitration_id == 0x200 and f.dlc == 4 and f.data[1] == 0,
        timeout_s,
    )
    bms_idle = _wait(
        can_adapter,
        lambda f: f.arbitration_id == 0x100 and f.dlc == 8 and f.data[6] == 2,
        timeout_s,
    )
    assert first_stop.timestamp <= max(evse_off.timestamp, bms_idle.timestamp)
    bms_gpioa = _read_odr(hil_config, "bms", 0x40020014)
    assert bms_gpioa & (1 << 8) == 0, f"BMS PA8 remains HIGH: ODR=0x{bms_gpioa:08X}"


@pytest.mark.hil
def test_tc_can_e2e_003_critical_fault_safe_off(
    can_adapter: CanAdapter, hil_config: dict[str, Any]
) -> None:
    """TC-CAN-E2E-003: critical BMS fault converges to EVSE command OFF."""

    command = str(hil_config.get("stimulus", {}).get("critical_fault_command", ""))
    if not command:
        pytest.skip("BLOCKED_INFRA: approved BMS fault injection is not configured")
    clear_command = str(
        hil_config.get("stimulus", {}).get("critical_fault_clear_command", "")
    )
    if not clear_command:
        pytest.skip("BLOCKED_INFRA: critical fault clear/recovery control is not configured")
    ExternalCommandController(command, "HIL_ALLOW_FAULT_INJECTION").trigger()
    try:
        fault_frame = _wait(
            can_adapter,
            lambda f: f.arbitration_id == 0x100
            and f.dlc == 8
            and f.data[5] == 0
            and bool(f.data[7] & 0x7F),
            3.0,
        )
        safe_frame = _wait(
            can_adapter,
            lambda f: f.arbitration_id == 0x200 and f.dlc == 4 and f.data[1] == 0,
            1.0,
        )
        measured_ms = (safe_frame.timestamp - fault_frame.timestamp) * 1000.0
        assert measured_ms >= 0.0
        # No upper limit is asserted until the requirement owner approves one.
        evse_gpioe = _read_odr(hil_config, "evse", 0x40021014)
        assert evse_gpioe & (1 << 11) == 0, (
            f"EVSE PE11 remains HIGH: ODR=0x{evse_gpioe:08X}"
        )
    finally:
        ExternalCommandController(
            clear_command, "HIL_ALLOW_FAULT_INJECTION"
        ).trigger()
