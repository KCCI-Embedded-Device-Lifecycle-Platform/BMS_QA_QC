"""EVSE bootloader binary protocol encoder/decoder for UART HIL."""

from __future__ import annotations

from dataclasses import dataclass

from hil.uart_adapter import UartAdapter

SOF = b"\xAA\x55"
CMD_START_UPDATE = 0x10
CMD_DATA = 0x11
CMD_END_UPDATE = 0x12
CMD_ABORT = 0x13
CMD_RUN_APP = 0x20
CMD_ACK = 0x79
CMD_NACK = 0x1F


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for octet in data:
        crc ^= octet << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def encode_packet(command: int, payload: bytes = b"", *, corrupt_crc: bool = False) -> bytes:
    if len(payload) > 512:
        raise ValueError("boot protocol payload exceeds 512 bytes")
    body = bytes([command]) + len(payload).to_bytes(2, "little") + payload
    crc = crc16_ccitt_false(body)
    if corrupt_crc:
        crc ^= 0x0001
    return SOF + body + crc.to_bytes(2, "little")


@dataclass(frozen=True, slots=True)
class BootPacket:
    command: int
    payload: bytes


class BootProtocolClient:
    def __init__(self, uart: UartAdapter) -> None:
        self.uart = uart

    def exchange(self, frame: bytes) -> BootPacket:
        self.uart.write(frame)
        if self.uart.read_exactly(2) != SOF:
            raise RuntimeError("boot response SOF mismatch")
        header = self.uart.read_exactly(3)
        command = header[0]
        length = int.from_bytes(header[1:3], "little")
        payload = self.uart.read_exactly(length)
        received_crc = int.from_bytes(self.uart.read_exactly(2), "little")
        if crc16_ccitt_false(header + payload) != received_crc:
            raise RuntimeError("boot response CRC mismatch")
        return BootPacket(command, payload)

    def request(self, command: int, payload: bytes = b"") -> BootPacket:
        return self.exchange(encode_packet(command, payload))
