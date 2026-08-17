from __future__ import annotations

import os
from typing import Any

import pytest

from hil.boot_protocol_client import CMD_NACK, CMD_START_UPDATE, encode_packet
from hil.ota_update_flow import (
    abort_failed_update,
    expect_crc_mismatch,
    image_crc32,
    run_application,
    successful_update,
    transfer_image,
)
from hil.tests.ota_support import enter_bootloader, open_binary_client, recovery_image


@pytest.mark.hil
@pytest.mark.destructive
def test_tc_ota_proto_002_corrupt_packet_crc_is_nack(hil_config: dict[str, Any]) -> None:
    """TC-OTA-PROTO-002: malformed CRC16 cannot initiate an update."""

    enter_bootloader(hil_config)
    start_payload = (8).to_bytes(4, "little") + (0).to_bytes(4, "little")
    adapter, client = open_binary_client(hil_config)
    try:
        response = client.exchange(
            encode_packet(CMD_START_UPDATE, start_payload, corrupt_crc=True)
        )
    finally:
        adapter.close()
    assert response.command == CMD_NACK


@pytest.mark.hil
@pytest.mark.destructive
def test_tc_ota_crc_001_whole_image_mismatch(hil_config: dict[str, Any]) -> None:
    """TC-OTA-CRC-001 rejects bad CRC, then restores the approved image."""

    if os.getenv("HIL_ALLOW_OTA_ERASE") != "YES":
        pytest.skip("BLOCKED_INFRA: HIL_ALLOW_OTA_ERASE=YES is required")
    image = recovery_image(hil_config)
    enter_bootloader(hil_config)
    adapter, client = open_binary_client(hil_config)
    try:
        mismatch = transfer_image(client, image, expected_crc32=image_crc32(image) ^ 1)
        expect_crc_mismatch(mismatch)
        abort_failed_update(client)
        evidence = successful_update(client, image)
        run_application(client, evidence.final_offset)
    finally:
        adapter.close()
