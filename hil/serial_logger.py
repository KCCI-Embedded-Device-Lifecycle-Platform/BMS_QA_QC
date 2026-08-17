"""Raw JSONL evidence logger using monotonic and wall-clock timestamps."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class EvidenceLogger:
    def __init__(self, path: str | Path, metadata: dict[str, Any]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self.path.open("w", encoding="utf-8", newline="\n")
        self.write("metadata", metadata)

    def write(self, event: str, payload: dict[str, Any]) -> None:
        record = {
            "wall_time_ns": time.time_ns(),
            "monotonic_ns": time.monotonic_ns(),
            "event": event,
            "payload": payload,
        }
        self._stream.write(json.dumps(record, sort_keys=True) + "\n")
        self._stream.flush()

    def close(self) -> None:
        self._stream.close()

    def __enter__(self) -> EvidenceLogger:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
