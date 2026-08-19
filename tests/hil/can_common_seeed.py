#!/usr/bin/env python3
"""Shared protocol and Seeed USB-CAN helpers for the BMS/EVSE bench test."""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from typing import Iterator, Optional

import can


BITRATE = 500_000
SERIAL_BAUDRATE = 2_000_000

ID_BMS_STATUS = 0x100
ID_BMS_FAULT = 0x101
ID_EVSE_STATUS = 0x200
ID_EVSE_CONTROL = 0x210
ID_TEST_REQUEST = 0x700
ID_BMS_TEST_RESPONSE = 0x701
ID_EVSE_TEST_RESPONSE = 0x702

TARGET_BMS = 0x01
TARGET_EVSE = 0x02

EVSE_STOP = 0x00
EVSE_START = 0x01

TEST_MAGIC = 0xA5


@dataclass(frozen=True)
class BmsStatus:
    voltage_v: float
    current_a: float
    soc_pct: int
    temperature_c: int
    fault_bits: int
    alive_counter: int


@dataclass(frozen=True)
class EvseStatus:
    state: int
    start_pressed: bool
    stop_pressed: bool
    fault_bits: int
    bms_alive: bool
    command_sequence: int
    alive_counter: int


def open_seeed_bus(
    channel: str,
    *,
    bitrate: int = BITRATE,
    operation_mode: str = "normal",
    frame_type: str = "STD",
) -> can.BusABC:
    """Open the Seeed 114991193 serial backend.

    The returned bus must be closed with bus.shutdown() or used through
    managed_seeed_bus().
    """
    return can.Bus(
        interface="seeedstudio",
        channel=channel,
        baudrate=SERIAL_BAUDRATE,
        bitrate=bitrate,
        frame_type=frame_type,
        operation_mode=operation_mode,
        timeout=0.1,
    )


@contextlib.contextmanager
def managed_seeed_bus(
    channel: str,
    *,
    bitrate: int = BITRATE,
    operation_mode: str = "normal",
    frame_type: str = "STD",
) -> Iterator[can.BusABC]:
    bus = open_seeed_bus(
        channel,
        bitrate=bitrate,
        operation_mode=operation_mode,
        frame_type=frame_type,
    )
    try:
        # Discard bytes left by an earlier abnormal process termination.
        flush = getattr(bus, "flush_buffer", None)
        if callable(flush):
            flush()
        yield bus
    finally:
        bus.shutdown()


def drain_rx(bus: can.BusABC, duration_s: float = 0.25) -> int:
    count = 0
    deadline = time.monotonic() + duration_s
    while time.monotonic() < deadline:
        if bus.recv(timeout=0.05) is not None:
            count += 1
    return count


def wait_for_id(
    bus: can.BusABC,
    arbitration_id: int,
    *,
    timeout_s: float,
    sequence: Optional[int] = None,
) -> Optional[can.Message]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        msg = bus.recv(timeout=0.1)
        if msg is None or msg.arbitration_id != arbitration_id:
            continue
        if sequence is not None and (msg.dlc < 8 or msg.data[7] != sequence):
            continue
        return msg
    return None


def build_test_request(target: int, sequence: int) -> can.Message:
    return can.Message(
        arbitration_id=ID_TEST_REQUEST,
        is_extended_id=False,
        data=[target, TEST_MAGIC, 0, 0, 0, 0, 0, sequence & 0xFF],
    )


def build_evse_control(command: int, sequence: int) -> can.Message:
    return can.Message(
        arbitration_id=ID_EVSE_CONTROL,
        is_extended_id=False,
        data=[command, sequence & 0xFF, 0, 0, 0, 0, 0, sequence & 0xFF],
    )


def decode_bms_status(msg: can.Message) -> BmsStatus:
    if msg.arbitration_id != ID_BMS_STATUS or msg.dlc != 8:
        raise ValueError("not an 8-byte BMS status frame")
    voltage_raw = int.from_bytes(msg.data[0:2], "little", signed=False)
    current_raw = int.from_bytes(msg.data[2:4], "little", signed=True)
    return BmsStatus(
        voltage_v=voltage_raw * 0.01,
        current_a=current_raw * 0.01,
        soc_pct=msg.data[4],
        temperature_c=msg.data[5] - 40,
        fault_bits=msg.data[6],
        alive_counter=msg.data[7],
    )


def decode_evse_status(msg: can.Message) -> EvseStatus:
    if msg.arbitration_id != ID_EVSE_STATUS or msg.dlc != 8:
        raise ValueError("not an 8-byte EVSE status frame")
    return EvseStatus(
        state=msg.data[0],
        start_pressed=bool(msg.data[1]),
        stop_pressed=bool(msg.data[2]),
        fault_bits=msg.data[3],
        bms_alive=bool(msg.data[4]),
        command_sequence=msg.data[6],
        alive_counter=msg.data[7],
    )


def frame_text(msg: can.Message) -> str:
    frame_type = "EXT" if msg.is_extended_id else "STD"
    return (
        f"{frame_type} ID=0x{msg.arbitration_id:03X} "
        f"DLC={msg.dlc} DATA={msg.data.hex(' ').upper()}"
    )
