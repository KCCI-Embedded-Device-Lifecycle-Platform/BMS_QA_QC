from __future__ import annotations

import os
from typing import Any

import pytest

from hil.ota_update_flow import run_application, successful_update
from hil.tests.ota_support import enter_bootloader, open_binary_client, recovery_image


@pytest.mark.hil
@pytest.mark.destructive
def test_tc_ota_update_001_valid_image_end_to_end(hil_config: dict[str, Any]) -> None:
    """TC-OTA-UPDATE-001: erase/write/CRC/vector commit and RUN_APP."""

    if os.getenv("HIL_ALLOW_OTA_ERASE") != "YES":
        pytest.skip("BLOCKED_INFRA: HIL_ALLOW_OTA_ERASE=YES is required")
    image = recovery_image(hil_config)
    enter_bootloader(hil_config)
    adapter, client = open_binary_client(hil_config)
    try:
        evidence = successful_update(client, image)
        assert evidence.final_offset == len(image)
        run_application(client, evidence.final_offset)
    finally:
        adapter.close()
