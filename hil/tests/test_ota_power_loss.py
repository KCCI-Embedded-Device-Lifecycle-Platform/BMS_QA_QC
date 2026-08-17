from __future__ import annotations

import pytest


@pytest.mark.hil
@pytest.mark.destructive
@pytest.mark.gap
def test_tc_ota_rollback_001_power_loss_recovery_policy_gap() -> None:
    """TC-OTA-ROLLBACK-001 is not executable before rollback policy exists."""

    pytest.skip(
        "GAP_REQUIREMENT: boot-failure count, rollback image, and power-loss recovery "
        "oracles are not approved; executing a power cut cannot produce PASS evidence"
    )
