#!/usr/bin/env python3
"""Capture non-invasive USB serial evidence before Raspberry Pi CAN HIL.

The script deliberately does not open or probe arbitrary serial ports.  On this
bench another ttyUSB device can be an ECU UART/bootloader, so guessing a CAN
channel would be unsafe and could invalidate the test evidence.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from serial.tools import list_ports


def _stable_links(device: Path) -> list[str]:
    links: list[str] = []
    for directory in (Path("/dev/serial/by-id"), Path("/dev/serial/by-path")):
        if not directory.is_dir():
            continue
        for candidate in sorted(directory.iterdir()):
            try:
                if candidate.resolve() == device.resolve():
                    links.append(str(candidate))
            except OSError:
                continue
    return links


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    ports = []
    for port in sorted(list_ports.comports(), key=lambda item: item.device):
        device = Path(port.device)
        ports.append(
            {
                "device": port.device,
                "description": port.description,
                "vid": port.vid,
                "pid": port.pid,
                "manufacturer": port.manufacturer,
                "product": port.product,
                "location": port.location,
                "stable_links": _stable_links(device),
            }
        )

    selected = Path(args.selected)
    result = {
        "selected_channel": args.selected,
        "selected_exists": selected.exists(),
        "selected_resolved": str(selected.resolve()) if selected.exists() else None,
        "ports": ports,
        "runner": os.getenv("CI_RUNNER_DESCRIPTION", ""),
        "job_id": os.getenv("CI_JOB_ID", ""),
        "commit": os.getenv("CI_COMMIT_SHA", ""),
        "classification_if_no_frames": "BLOCKED_INFRA",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

    if not result["selected_exists"]:
        print(f"BLOCKED_INFRA: selected CAN channel does not exist: {args.selected}")
        return 2
    print("PREFLIGHT=PASS selected CAN channel exists; passive frame evidence still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
