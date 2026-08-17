"""Reviewed OTA transfer flow with explicit ACK offsets and recovery support."""

from __future__ import annotations

import hashlib
import zlib
from dataclasses import dataclass

from hil.boot_protocol_client import (
    CMD_ABORT,
    CMD_ACK,
    CMD_DATA,
    CMD_END_UPDATE,
    CMD_NACK,
    CMD_RUN_APP,
    CMD_START_UPDATE,
    BootPacket,
    BootProtocolClient,
)


@dataclass(frozen=True, slots=True)
class UpdateEvidence:
    image_sha256: str
    image_crc32: int
    image_size: int
    final_offset: int


def image_crc32(image: bytes) -> int:
    return zlib.crc32(image) & 0xFFFFFFFF


def _expect_ack(packet: BootPacket, request_command: int, next_offset: int) -> None:
    if packet.command != CMD_ACK:
        raise AssertionError(
            f"command 0x{request_command:02X} expected ACK, got 0x{packet.command:02X}"
        )
    if len(packet.payload) != 6 or packet.payload[0] != request_command:
        raise AssertionError(f"malformed ACK payload: {packet.payload.hex()}")
    reported_offset = int.from_bytes(packet.payload[2:6], "little")
    if reported_offset != next_offset:
        raise AssertionError(f"ACK next_offset={reported_offset}, expected={next_offset}")


def transfer_image(
    client: BootProtocolClient,
    image: bytes,
    *,
    expected_crc32: int | None = None,
) -> BootPacket:
    if len(image) < 8:
        raise ValueError("recovery image is smaller than an STM32 vector table")
    expected = image_crc32(image) if expected_crc32 is None else expected_crc32
    start = client.request(
        CMD_START_UPDATE,
        len(image).to_bytes(4, "little") + expected.to_bytes(4, "little"),
    )
    _expect_ack(start, CMD_START_UPDATE, 0)

    offset = 0
    while offset < len(image):
        chunk = image[offset : offset + 508]
        response = client.request(CMD_DATA, offset.to_bytes(4, "little") + chunk)
        offset += len(chunk)
        _expect_ack(response, CMD_DATA, offset)
    return client.request(CMD_END_UPDATE)


def successful_update(client: BootProtocolClient, image: bytes) -> UpdateEvidence:
    end = transfer_image(client, image)
    _expect_ack(end, CMD_END_UPDATE, len(image))
    return UpdateEvidence(
        image_sha256=hashlib.sha256(image).hexdigest(),
        image_crc32=image_crc32(image),
        image_size=len(image),
        final_offset=len(image),
    )


def abort_failed_update(client: BootProtocolClient) -> None:
    response = client.request(CMD_ABORT)
    _expect_ack(response, CMD_ABORT, 0)


def run_application(client: BootProtocolClient, final_offset: int) -> None:
    response = client.request(CMD_RUN_APP)
    _expect_ack(response, CMD_RUN_APP, final_offset)


def expect_crc_mismatch(packet: BootPacket) -> None:
    # Product enum AP_BOOT_UPDATE_ERROR_CRC_MISMATCH is 13 in the approved SHA.
    if packet.command != CMD_NACK or len(packet.payload) != 7:
        raise AssertionError(f"expected update NACK, got {packet}")
    if packet.payload[0] != CMD_END_UPDATE or packet.payload[1] != 13:
        raise AssertionError(f"expected CRC_MISMATCH NACK, got {packet.payload.hex()}")
