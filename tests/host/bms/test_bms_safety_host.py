from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.host.common.build_c_harness import CBuildError, compile_executable, run_case
from tests.host.common.product_paths import QA_ROOT, bms_product_dir

BMS_FAULT_CASES = [
    "TC-BMS-OV-001",
    "TC-BMS-OV-002",
    "TC-BMS-OV-003",
    "TC-BMS-OV-004",
    "TC-BMS-UV-001",
    "TC-BMS-PACKOV-001",
    "TC-BMS-OC-001",
    "TC-BMS-OT-001",
    "TC-BMS-SENSOR-001",
    "TC-BMS-PERMIT-001",
    "TC-BMS-MULTI-001",
]


@pytest.fixture(scope="session")
def bms_fault_harness(tmp_path_factory: pytest.TempPathFactory) -> Path:
    product = bms_product_dir()
    output = tmp_path_factory.mktemp("bms-host") / "bms_fault_host"
    try:
        return compile_executable(
            output=output,
            sources=[
                product / "BMS/app/bms_fault.c",
                QA_ROOT / "firmware/bms/bms_oracle.c",
                QA_ROOT / "tests/host/bms/mocks/hw_tick_mock.c",
                QA_ROOT / "tests/host/bms/test_bms_fault.c",
            ],
            includes=[
                QA_ROOT / "tests/host/bms/mocks",
                QA_ROOT / "firmware/common",
                QA_ROOT / "firmware/bms",
                product / "BMS/common",
                product / "BMS/app",
                product / "BMS/hw",
            ],
        )
    except CBuildError as exc:
        pytest.fail(f"MISMATCH_CONFIGURATION: {exc}")


@pytest.mark.host
@pytest.mark.parametrize("test_id", BMS_FAULT_CASES)
def test_bms_fault_requirement(bms_fault_harness: Path, test_id: str) -> None:
    completed = run_case(bms_fault_harness, test_id)
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.host
def test_tc_bms_fsm_001(tmp_path: Path) -> None:
    product = bms_product_dir()
    try:
        executable = compile_executable(
            output=tmp_path / "bms_fsm_host",
            sources=[product / "BMS/app/bms_state.c", Path(__file__).with_name("test_bms_fsm.c")],
            includes=[
                QA_ROOT / "tests/host/bms/mocks",
                product / "BMS/common",
                product / "BMS/app",
                product / "BMS/hw",
            ],
        )
    except CBuildError as exc:
        pytest.fail(f"MISMATCH_CONFIGURATION: {exc}")
    completed = subprocess.run(
        [str(executable)], capture_output=True, text=True, check=False, timeout=20
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
