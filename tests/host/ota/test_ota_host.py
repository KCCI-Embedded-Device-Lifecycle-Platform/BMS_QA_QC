from __future__ import annotations

from pathlib import Path

import pytest

from tests.host.common.build_c_harness import compile_executable, run_case
from tests.host.common.product_paths import QA_ROOT, ota_boot_dir


@pytest.fixture(scope="session")
def ota_protocol_executable(tmp_path_factory: pytest.TempPathFactory) -> Path:
    product = ota_boot_dir()
    build_dir = tmp_path_factory.mktemp("ota-protocol-c")
    return compile_executable(
        output=build_dir / "test_ota_protocol",
        sources=[
            QA_ROOT / "tests/host/ota/test_ota_protocol.c",
            product / "Middleware/boot_protocol.c",
            product / "Middleware/boot_crc16.c",
        ],
        includes=[product],
    )


@pytest.fixture(scope="session")
def ota_update_executable(tmp_path_factory: pytest.TempPathFactory) -> Path:
    product = ota_boot_dir()
    build_dir = tmp_path_factory.mktemp("ota-update-c")
    return compile_executable(
        output=build_dir / "test_ota_update",
        sources=[
            QA_ROOT / "tests/host/ota/test_ota_update.c",
            QA_ROOT / "tests/host/ota/mocks/bsp_storage_mock.c",
            QA_ROOT / "bootloader/ota_oracle.c",
            product / "App/ap_boot_update.c",
            product / "App/ap_boot_command.c",
            product / "Middleware/boot_crc32.c",
        ],
        includes=[
            QA_ROOT / "tests/host/ota/mocks",
            QA_ROOT / "bootloader",
            QA_ROOT / "firmware/common",
            product,
        ],
    )


@pytest.mark.host
@pytest.mark.parametrize("case_id", ["TC-OTA-PROTO-001", "TC-OTA-PROTO-002"])
def test_boot_protocol(ota_protocol_executable: Path, case_id: str) -> None:
    completed = run_case(ota_protocol_executable, case_id)
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.host
@pytest.mark.parametrize(
    "case_id",
    [
        "TC-OTA-SIZE-001",
        "TC-OTA-OFFSET-001",
        "TC-OTA-CRC-001",
        "TC-OTA-UPDATE-001",
        "TC-OTA-PROTO-001",
    ],
)
def test_boot_update_component(ota_update_executable: Path, case_id: str) -> None:
    completed = run_case(ota_update_executable, case_id)
    assert completed.returncode == 0, completed.stdout + completed.stderr
