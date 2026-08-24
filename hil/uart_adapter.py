"""Small, timeout-bounded UART adapter for bootloader HIL."""

from __future__ import annotations

from dataclasses import dataclass


class UartAdapterError(RuntimeError):
    pass


@dataclass(slots=True)
class UartConfig:
    port: str
    baudrate: int = 115_200
    timeout_s: float = 1.0


class UartAdapter:
    def __init__(self, config: UartConfig) -> None:
        try:
            import serial
        except ImportError as exc:
            raise UartAdapterError("pyserial is required for bootloader HIL") from exc
        try:
            self._serial = serial.Serial(
                port=config.port,
                baudrate=config.baudrate,
                timeout=config.timeout_s,
                write_timeout=config.timeout_s,
            )
        except Exception as exc:
            raise UartAdapterError(f"cannot open UART {config.port!r}: {exc}") from exc

    def write(self, data: bytes) -> None:
        written = self._serial.write(data)
        self._serial.flush()
        if written != len(data):
            raise UartAdapterError(f"short UART write: {written}/{len(data)}")

    def reset_input_buffer(self) -> None:
        self._serial.reset_input_buffer()

    def read_exactly(self, length: int) -> bytes:
        data = self._serial.read(length)
        if len(data) != length:
            raise UartAdapterError(f"UART timeout: expected {length} bytes, got {len(data)}")
        return data

    def read_until(self, terminator: bytes = b"\n", maximum: int = 256) -> bytes:
        data = self._serial.read_until(terminator, maximum)
        if not data.endswith(terminator):
            raise UartAdapterError("UART line terminator not received before timeout")
        return data

    def close(self) -> None:
        self._serial.close()

    def __enter__(self) -> UartAdapter:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
