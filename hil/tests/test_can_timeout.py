from __future__ import annotations

import statistics
import time
from collections import defaultdict
from typing import Any

import pytest

from hil.can_adapter import CanAdapter
from hil.openocd_client import OpenOcdClient
from hil.power_fault_controller import ExternalCommandController
from hil.tests.support import collect_frames, wait_for_frame


@pytest.mark.hil
def test_tc_can_hb_001_periodicity(
    can_adapter: CanAdapter, hil_config: dict[str, Any]
) -> None:
    """TC-CAN-HB-001: verify the approved periodic frame schedule."""

    observation_s = float(hil_config.get("timing", {}).get("observation_s", 4.0))
    tolerance = float(hil_config.get("timing", {}).get("relative_tolerance", 0.35))
    expected_periods = {
        0x100: 0.100,
        0x101: 0.500,
        0x102: 0.500,
        0x103: 0.100,
        0x104: 1.000,
        0x200: 0.100,
        0x201: 0.100,
        0x202: 0.100,
    }
    samples: dict[int, list[float]] = defaultdict(list)
    for frame in collect_frames(can_adapter, observation_s):
        if (
            frame.arbitration_id in expected_periods
            and not frame.is_extended_id
            and not frame.is_remote_frame
            and not frame.is_error_frame
        ):
            samples[frame.arbitration_id].append(frame.timestamp)

    failures: list[str] = []
    for arbitration_id, expected in expected_periods.items():
        timestamps = samples[arbitration_id]
        if len(timestamps) < 2:
            failures.append(f"0x{arbitration_id:03X}: fewer than two frames")
            continue
        intervals = [right - left for left, right in zip(timestamps, timestamps[1:], strict=False)]
        median = statistics.median(intervals)
        if abs(median - expected) > expected * tolerance:
            failures.append(
                f"0x{arbitration_id:03X}: median={median:.4f}s expected={expected:.4f}s"
            )
    assert not failures, "\n".join(failures)


@pytest.mark.hil
def test_tc_bms_link_001_timeout_and_recovery(
    can_adapter: CanAdapter, hil_config: dict[str, Any]
) -> None:
    """TC-BMS-LINK-001: isolate EVSE TX, then observe timeout and recovery."""

    stimulus = hil_config.get("stimulus", {})
    silence = str(stimulus.get("evse_silence_command", ""))
    restore = str(stimulus.get("evse_restore_command", ""))
    if not silence or not restore:
        pytest.skip("BLOCKED_INFRA: EVSE silence/restore controls are not configured")

    wait_for_frame(can_adapter, lambda frame: frame.arbitration_id == 0x100, 2.0)
    ExternalCommandController(silence, "HIL_ALLOW_LINK_FAULT").trigger()
    silence_start = time.monotonic()
    try:
        timeout_frame = wait_for_frame(
            can_adapter,
            lambda frame: frame.arbitration_id == 0x100
            and frame.dlc == 8
            and bool(frame.data[7] & 0x40),
            2.0,
        )
        elapsed_ms = (timeout_frame.timestamp - silence_start) * 1000.0
        assert 1000.0 <= elapsed_ms <= 1100.0, f"measured timeout {elapsed_ms:.1f}ms"
    finally:
        ExternalCommandController(restore, "HIL_ALLOW_LINK_FAULT").trigger()

    recovery_start = time.monotonic()
    recovered = wait_for_frame(
        can_adapter,
        lambda frame: frame.arbitration_id == 0x100
        and frame.dlc == 8
        and not bool(frame.data[7] & 0x40),
        1.5,
    )
    recovery_ms = (recovered.timestamp - recovery_start) * 1000.0
    assert 300.0 <= recovery_ms <= 400.0, f"measured link recovery {recovery_ms:.1f}ms"


@pytest.mark.hil
def test_tc_evse_safe_004_bms_timeout_drives_pe11_low(
    can_adapter: CanAdapter, hil_config: dict[str, Any]
) -> None:
    """TC-EVSE-SAFE-004: no BMS main frame for >500 ms drives PE11 LOW."""

    stimulus = hil_config.get("stimulus", {})
    silence = str(stimulus.get("bms_silence_command", ""))
    restore = str(stimulus.get("bms_restore_command", ""))
    if not silence or not restore:
        pytest.skip("BLOCKED_INFRA: BMS silence/restore controls are not configured")

    wait_for_frame(
        can_adapter,
        lambda frame: frame.arbitration_id == 0x200
        and frame.dlc == 4
        and frame.data[1] == 1,
        3.0,
    )
    last_bms = wait_for_frame(
        can_adapter, lambda frame: frame.arbitration_id == 0x100 and frame.dlc == 8, 2.0
    )
    ExternalCommandController(silence, "HIL_ALLOW_LINK_FAULT").trigger()
    try:
        safe_frame = wait_for_frame(
            can_adapter,
            lambda frame: frame.arbitration_id == 0x200
            and frame.dlc == 4
            and frame.data[1] == 0,
            1.5,
        )
        elapsed_ms = (safe_frame.timestamp - last_bms.timestamp) * 1000.0
        assert 500.0 <= elapsed_ms <= 650.0, f"measured Safe-Off {elapsed_ms:.1f}ms"

        openocd = hil_config.get("openocd", {}).get("evse", {})
        with OpenOcdClient(
            host=str(openocd.get("host", "127.0.0.1")),
            port=int(openocd.get("port", 4444)),
        ) as client:
            gpioe_odr = client.read_word(0x40021014)
        assert gpioe_odr & (1 << 11) == 0, f"PE11 remains HIGH: ODR=0x{gpioe_odr:08X}"
    finally:
        ExternalCommandController(restore, "HIL_ALLOW_LINK_FAULT").trigger()
