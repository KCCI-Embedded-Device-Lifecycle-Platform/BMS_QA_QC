"""Gateway tests remain executable BLOCKED records until its ICD is approved."""

import pytest

CASES = [
    "TC-GA-DECODE-001",
    "TC-GA-STATE-001",
    "TC-GA-STALE-001",
    "TC-GA-INVALID-001",
    "TC-GA-LOG-001",
]


@pytest.mark.gap
@pytest.mark.parametrize("test_id", CASES, ids=CASES)
def test_gateway_contract_waiting(test_id: str) -> None:
    pytest.skip(
        f"BLOCKED_INFRA {test_id}: gateway input/output schema and source boundary are not approved"
    )
