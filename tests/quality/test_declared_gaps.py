"""Executable documentation for requirements that are not implemented.

Skipping is intentional: it prevents an absent product feature from being
misreported as PASS while still creating a visible JUnit record.
"""

import pytest

GAPS = {
    "TC-OTA-VERSION-001": "image version/anti-downgrade contract is not approved",
    "TC-OTA-ROLLBACK-001": "power-loss rollback/dual-bank recovery is not implemented",
    "TC-OTA-XTARGET-001": "signed target identity binding is not implemented",
}


@pytest.mark.gap
@pytest.mark.parametrize("test_id,reason", GAPS.items(), ids=GAPS)
def test_product_requirement_gap(test_id: str, reason: str) -> None:
    pytest.skip(f"GAP_REQUIREMENT {test_id}: {reason}")
