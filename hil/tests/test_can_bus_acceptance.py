from __future__ import annotations

import time
from typing import Any

import pytest

from hil.can_adapter import CanAdapter


@pytest.mark.hil
def test_tc_can_bus_001_three_node_acceptance(
    can_adapter: CanAdapter, hil_config: dict[str, Any]
) -> None:
    """TC-CAN-BUS-001: both ECUs are visible on the approved 500 kbit/s bus.

    Resistance is fixture evidence, not something SocketCAN can measure.  The
    operator therefore records the DMM value in HIL_CONFIG before this test.
    """

    resistance = hil_config.get("fixture", {}).get("termination_ohms")
    if resistance is None:
        pytest.skip("BLOCKED_INFRA: fixture.termination_ohms DMM evidence is missing")
    assert 54.0 <= float(resistance) <= 66.0

    seen_bms = False
    seen_evse = False
    error_frames = 0
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        frame = can_adapter.recv(min(0.2, deadline - time.monotonic()))
        if frame is None:
            continue
        error_frames += int(frame.is_error_frame)
        seen_bms |= frame.arbitration_id in range(0x100, 0x106)
        seen_evse |= frame.arbitration_id in range(0x200, 0x203)
    assert seen_bms and seen_evse, f"node visibility bms={seen_bms} evse={seen_evse}"
    assert error_frames == 0, f"observed {error_frames} CAN error frames"
