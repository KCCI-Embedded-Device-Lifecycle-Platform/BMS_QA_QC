from __future__ import annotations

import time
from collections.abc import Callable

from hil.can_adapter import CanAdapter, CanFrame


def collect_frames(
    adapter: CanAdapter,
    duration_s: float,
    predicate: Callable[[CanFrame], bool] | None = None,
) -> list[CanFrame]:
    frames: list[CanFrame] = []
    deadline = time.monotonic() + duration_s
    while time.monotonic() < deadline:
        frame = adapter.recv(min(0.2, max(0.0, deadline - time.monotonic())))
        if frame is None:
            continue
        if predicate is None or predicate(frame):
            frames.append(frame)
    return frames


def wait_for_frame(
    adapter: CanAdapter,
    predicate: Callable[[CanFrame], bool],
    timeout_s: float,
) -> CanFrame:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        frame = adapter.recv(min(0.2, max(0.0, deadline - time.monotonic())))
        if frame is not None and predicate(frame):
            return frame
    raise AssertionError(f"expected CAN frame was not observed within {timeout_s:.3f}s")
