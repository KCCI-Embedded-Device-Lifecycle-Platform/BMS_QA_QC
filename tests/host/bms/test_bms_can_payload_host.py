from __future__ import annotations

from pathlib import Path

import pytest

from tests.host.common.build_c_harness import CBuildError, compile_executable, run_case
from tests.host.common.product_paths import QA_ROOT, bms_product_dir


@pytest.mark.host
def test_tc_can_host_001_bms_product_payload(tmp_path: Path) -> None:
    """BEOG-36: compile and execute the real BMS payload packer on Ubuntu."""

    product = bms_product_dir()
    try:
        executable = compile_executable(
            output=tmp_path / "bms_can_payload_host",
            sources=[
                product / "BMS/app/bms_link.c",
                Path(__file__).with_name("test_bms_can_payload.c"),
            ],
            includes=[
                QA_ROOT / "tests/host/bms/mocks",
                product / "BMS/common",
                product / "BMS/app",
                product / "BMS/hw",
            ],
        )
    except CBuildError as exc:
        pytest.fail(f"MISMATCH_CONFIGURATION: {exc}")

    completed = run_case(executable, "TC-CAN-HOST-001")
    assert completed.returncode == 0, completed.stdout + completed.stderr
