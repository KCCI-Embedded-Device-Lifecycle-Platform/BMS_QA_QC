from __future__ import annotations

import sys
from types import ModuleType

import pytest

from hil.can_adapter import create_can_adapter


@pytest.mark.host
def test_seeed_transport_uses_qualified_serial_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeBus:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)
            self.flushed = False

        def flush_buffer(self) -> None:
            self.flushed = True

        def shutdown(self) -> None:
            pass

    fake_can = ModuleType("can")

    def fake_bus_factory(**kwargs: object) -> FakeBus:
        return FakeBus(**kwargs)

    fake_can.Bus = fake_bus_factory  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "can", fake_can)

    adapter = create_can_adapter(
        {
            "interface": "seeedstudio",
            "channel": "/dev/serial/by-id/qa-can",
            "bitrate": 500_000,
        }
    )
    try:
        assert captured == {
            "interface": "seeedstudio",
            "channel": "/dev/serial/by-id/qa-can",
            "bitrate": 500_000,
            "frame_type": "STD",
            "operation_mode": "normal",
            "baudrate": 2_000_000,
            "timeout": 0.1,
        }
        assert adapter._bus.flushed  # type: ignore[attr-defined]
    finally:
        adapter.close()
