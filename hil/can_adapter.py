"""CAN adapters with one contract for SocketCAN and Seeed USB-CAN.

The Raspberry Pi bench currently receives through the python-can ``seeedstudio``
backend on ``/dev/ttyUSB0``.  A SocketCAN backend is also provided for MCP2515,
gs_usb, or another adapter that exposes ``can0``.  Tests must not silently switch
between them because that would turn an infrastructure mismatch into a product
failure.
"""

from __future__ import annotations

import socket
import struct
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

CAN_SFF_MASK = 0x7FF
CAN_EFF_FLAG = 0x80000000
CAN_RTR_FLAG = 0x40000000
CAN_ERR_FLAG = 0x20000000
_LINUX_CAN_FRAME = struct.Struct("=IB3x8s")


class CanAdapterError(RuntimeError):
    """Infrastructure failure while opening or using the CAN adapter."""


@dataclass(frozen=True, slots=True)
class CanFrame:
    arbitration_id: int
    data: bytes
    timestamp: float
    is_extended_id: bool = False
    is_remote_frame: bool = False
    is_error_frame: bool = False

    @property
    def dlc(self) -> int:
        return len(self.data)


class CanAdapter(ABC):
    @abstractmethod
    def recv(self, timeout: float) -> CanFrame | None:
        """Receive one frame, returning ``None`` on timeout."""

    @abstractmethod
    def send(self, arbitration_id: int, data: bytes) -> None:
        """Send one standard data frame."""

    @abstractmethod
    def close(self) -> None:
        """Release the adapter."""

    def __enter__(self) -> CanAdapter:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


class SocketCanAdapter(CanAdapter):
    def __init__(self, channel: str) -> None:
        if not hasattr(socket, "PF_CAN"):
            raise CanAdapterError("SocketCAN is unavailable on this operating system")
        self._socket = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        try:
            self._socket.bind((channel,))
        except OSError as exc:
            self._socket.close()
            raise CanAdapterError(f"cannot bind SocketCAN channel {channel!r}: {exc}") from exc

    def recv(self, timeout: float) -> CanFrame | None:
        self._socket.settimeout(timeout)
        try:
            raw = self._socket.recv(_LINUX_CAN_FRAME.size)
        except TimeoutError:
            return None
        except OSError as exc:
            raise CanAdapterError(f"SocketCAN receive failed: {exc}") from exc

        can_id, dlc, payload = _LINUX_CAN_FRAME.unpack(raw)
        if dlc > 8:
            raise CanAdapterError(f"classic CAN frame reported invalid DLC {dlc}")
        return CanFrame(
            arbitration_id=can_id & CAN_SFF_MASK,
            data=payload[:dlc],
            timestamp=time.monotonic(),
            is_extended_id=bool(can_id & CAN_EFF_FLAG),
            is_remote_frame=bool(can_id & CAN_RTR_FLAG),
            is_error_frame=bool(can_id & CAN_ERR_FLAG),
        )

    def send(self, arbitration_id: int, data: bytes) -> None:
        _validate_standard_frame(arbitration_id, data)
        raw = _LINUX_CAN_FRAME.pack(arbitration_id, len(data), data.ljust(8, b"\x00"))
        try:
            self._socket.send(raw)
        except OSError as exc:
            raise CanAdapterError(f"SocketCAN send failed: {exc}") from exc

    def close(self) -> None:
        self._socket.close()


class PythonCanAdapter(CanAdapter):
    def __init__(self, *, interface: str, channel: str, bitrate: int, **kwargs: Any) -> None:
        try:
            import can
        except ImportError as exc:
            raise CanAdapterError("python-can is required for this adapter") from exc
        try:
            self._can = can
            self._bus = can.Bus(
                interface=interface,
                channel=channel,
                bitrate=bitrate,
                **kwargs,
            )
            # A previous interrupted Runner job can leave complete protocol
            # frames in the Seeed serial receive buffer.  Start every evidence
            # window from a known boundary, matching the proven bench utility.
            flush = getattr(self._bus, "flush_buffer", None)
            if callable(flush):
                flush()
        except Exception as exc:  # python-can exposes backend-specific exception types.
            raise CanAdapterError(
                f"cannot open python-can interface={interface!r} channel={channel!r}: {exc}"
            ) from exc

    def recv(self, timeout: float) -> CanFrame | None:
        try:
            message = self._bus.recv(timeout=timeout)
        except Exception as exc:
            raise CanAdapterError(f"python-can receive failed: {exc}") from exc
        if message is None:
            return None
        return CanFrame(
            arbitration_id=int(message.arbitration_id),
            data=bytes(message.data),
            timestamp=time.monotonic(),
            is_extended_id=bool(message.is_extended_id),
            is_remote_frame=bool(message.is_remote_frame),
            is_error_frame=bool(message.is_error_frame),
        )

    def send(self, arbitration_id: int, data: bytes) -> None:
        _validate_standard_frame(arbitration_id, data)
        message = self._can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=False,
        )
        try:
            self._bus.send(message)
        except Exception as exc:
            raise CanAdapterError(f"python-can send failed: {exc}") from exc

    def close(self) -> None:
        self._bus.shutdown()


def _validate_standard_frame(arbitration_id: int, data: bytes) -> None:
    if not 0 <= arbitration_id <= CAN_SFF_MASK:
        raise ValueError(f"standard CAN ID out of range: 0x{arbitration_id:X}")
    if len(data) > 8:
        raise ValueError(f"classic CAN payload exceeds 8 bytes: {len(data)}")


def create_can_adapter(config: dict[str, Any]) -> CanAdapter:
    """Create only the explicitly configured backend.

    No fallback is attempted.  A missing ``can0`` and a missing ``/dev/ttyUSB0``
    are different infrastructure failures and must remain distinguishable.
    """

    interface = str(config.get("interface", "socketcan"))
    channel = str(config.get("channel", "can0"))
    bitrate = int(config.get("bitrate", 500_000))
    if bitrate != 500_000:
        raise CanAdapterError(f"approved BMS-EVSE bitrate is 500000, got {bitrate}")
    if interface == "socketcan":
        return SocketCanAdapter(channel)

    extra: dict[str, Any] = {}
    if interface == "seeedstudio":
        extra.update(
            frame_type=str(config.get("frame_type", "STD")),
            operation_mode=str(config.get("operation_mode", "normal")),
            # This is the USB serial transport rate, not the 500 kbit/s CAN
            # bus rate.  Seeed 114991193 bench reception was qualified at 2 Mbaud.
            baudrate=int(config.get("serial_baudrate", 2_000_000)),
            timeout=float(config.get("timeout_s", 0.1)),
        )
    return PythonCanAdapter(interface=interface, channel=channel, bitrate=bitrate, **extra)
