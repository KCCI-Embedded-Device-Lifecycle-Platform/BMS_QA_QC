from __future__ import annotations

from typing import Any

import pytest

from hil.can_adapter import CanAdapter
from hil.power_fault_controller import ExternalCommandController
from hil.tests.support import wait_for_frame


@pytest.mark.hil
@pytest.mark.destructive
def test_tc_can_busoff_001_detect_and_recover(
    can_adapter: CanAdapter, hil_config: dict[str, Any]
) -> None:
    """TC-CAN-BUSOFF-001: requires a reviewed physical bus fault fixture."""

    stimulus = hil_config.get("stimulus", {})
    enter = str(stimulus.get("bus_fault_command", ""))
    restore = str(stimulus.get("bus_restore_command", ""))
    if not enter or not restore:
        pytest.skip("BLOCKED_INFRA: bus fault/restore fixture is not configured")

    ExternalCommandController(enter, "HIL_ALLOW_BUS_FAULT").trigger()
    try:
        # EVSE reports CAN_BUS_OFF through 0x202 bit 4 when it can transmit again.
        pass
    finally:
        ExternalCommandController(restore, "HIL_ALLOW_BUS_FAULT").trigger()

    fault = wait_for_frame(
        can_adapter,
        lambda frame: frame.arbitration_id == 0x202
        and frame.dlc == 1
        and bool(frame.data[0] & 0x10),
        3.0,
    )
    assert fault.data[0] & 0x10
    wait_for_frame(can_adapter, lambda frame: frame.arbitration_id == 0x200, 3.0)
