from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.host.common.build_c_harness import CBuildError, compile_executable, run_case
from tests.host.common.product_paths import QA_ROOT, evse_product_dir

CORE_CASES = [
    "TC-CAN-PROTO-001",
    "TC-CAN-ENDIAN-001",
    "TC-CAN-NEG-001",
    "TC-CAN-UNKID-001",
    "TC-CAN-E2E-001",
    "TC-EVSE-SAFE-001",
    "TC-EVSE-SAFE-002",
    "TC-EVSE-SAFE-003",
    "TC-EVSE-SAFE-004",
    "TC-EVSE-SAFE-005",
    "TC-EVSE-SAFE-006",
    "TC-EVSE-FAULT-001",
    "TC-EVSE-CAN-REQ-001",
]


@pytest.fixture(scope="session")
def evse_core_harness(tmp_path_factory: pytest.TempPathFactory) -> Path:
    product = evse_product_dir()
    try:
        return compile_executable(
            output=tmp_path_factory.mktemp("evse-host") / "evse_core_host",
            sources=[
                product / "MyApp/Common/can_protocol.c",
                product / "MyApp/Application/evse_fsm.c",
                QA_ROOT / "firmware/evse/evse_oracle.c",
                QA_ROOT / "tests/host/evse/test_evse_core.c",
            ],
            includes=[
                QA_ROOT / "firmware/common",
                QA_ROOT / "firmware/evse",
                product / "MyApp/Common",
                product / "MyApp/Application",
            ],
        )
    except CBuildError as exc:
        pytest.fail(f"MISMATCH_CONFIGURATION: {exc}")


@pytest.mark.host
@pytest.mark.parametrize("test_id", CORE_CASES)
def test_evse_core_requirement(evse_core_harness: Path, test_id: str) -> None:
    completed = run_case(evse_core_harness, test_id)
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.host
def test_tc_evse_in_001(tmp_path: Path) -> None:
    product = evse_product_dir()
    try:
        executable = compile_executable(
            output=tmp_path / "evse_input_host",
            sources=[
                product / "MyApp/Driver/evse_input.c",
                QA_ROOT / "tests/host/evse/mocks/evse_gpio_mock.c",
                QA_ROOT / "tests/host/evse/test_evse_input.c",
            ],
            includes=[
                QA_ROOT / "tests/host/evse/mocks",
                QA_ROOT / "firmware/common",
                product / "MyApp/Common",
                product / "MyApp/Driver",
            ],
        )
    except CBuildError as exc:
        pytest.fail(f"MISMATCH_CONFIGURATION: {exc}")
    completed = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
