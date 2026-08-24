"""Minimal ISO-TP/UDS client kept inactive until a UDS requirement is approved.

The reviewed catalog deliberately excludes decorative UDS PASS cases.  This
client is infrastructure only; no UDS test is marked executable until CAN IDs,
timings, sessions, DIDs, and negative response behavior are baselined.
"""

from __future__ import annotations

import time

from hil.can_adapter import CanAdapter


class IsoTpError(RuntimeError):
    pass


class IsoTpUdsClient:
    def __init__(
        self,
        adapter: CanAdapter,
        *,
        request_id: int,
        response_id: int,
        timeout_s: float = 1.0,
    ) -> None:
        self.adapter = adapter
        self.request_id = request_id
        self.response_id = response_id
        self.timeout_s = timeout_s

    def request_single_frame(self, payload: bytes) -> bytes:
        if not 1 <= len(payload) <= 7:
            raise ValueError("this safety-limited client sends only ISO-TP single frames")
        self.adapter.send(self.request_id, bytes([len(payload)]) + payload)
        deadline = time.monotonic() + self.timeout_s
        while time.monotonic() < deadline:
            frame = self.adapter.recv(max(0.0, deadline - time.monotonic()))
            if frame is None or frame.arbitration_id != self.response_id:
                continue
            if frame.is_extended_id or frame.is_remote_frame or frame.dlc < 2:
                continue
            pci_length = frame.data[0] & 0x0F
            if frame.data[0] >> 4 != 0 or not 1 <= pci_length <= 7:
                raise IsoTpError("response is not a valid ISO-TP single frame")
            if frame.dlc < pci_length + 1:
                raise IsoTpError("truncated ISO-TP response")
            return frame.data[1 : 1 + pci_length]
        raise IsoTpError("UDS response timeout")
