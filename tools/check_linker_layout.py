#!/usr/bin/env python3
"""Fail CI when a FLASH linker region overlaps an approved reserved region."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FLASH = re.compile(
    r"FLASH\s*\([^)]*\)\s*:\s*ORIGIN\s*=\s*(0x[0-9A-Fa-f]+)\s*,\s*LENGTH\s*=\s*([0-9]+)([KkMm]?)"
)


def find_linker_file(path: Path) -> Path:
    if path.is_file():
        return path
    if path.parent.is_dir():
        target_lower = path.name.lower()
        for candidate in path.parent.iterdir():
            if candidate.is_file() and candidate.name.lower() == target_lower:
                return candidate
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--linker", required=True, type=Path)
    parser.add_argument("--origin", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--end", required=True, type=lambda value: int(value, 0))
    args = parser.parse_args()

    linker_file = find_linker_file(args.linker)
    if not linker_file.is_file():
        raise SystemExit(f"linker script not found: {args.linker}")

    text = linker_file.read_text(encoding="utf-8", errors="replace")
    match = FLASH.search(text)
    if match is None:
        raise SystemExit("cannot locate FLASH ORIGIN/LENGTH in linker script")
    origin = int(match.group(1), 0)
    length = int(match.group(2))
    suffix = match.group(3).upper()
    if suffix == "K":
        length *= 1024
    elif suffix == "M":
        length *= 1024 * 1024
    if origin != args.origin:
        raise SystemExit(f"FLASH origin 0x{origin:08X}, expected 0x{args.origin:08X}")
    if origin + length > args.end:
        raise SystemExit(
            f"FLASH end 0x{origin + length:08X} overlaps reserved region at 0x{args.end:08X}"
        )
    print(f"PASS linker ({linker_file.name}) origin=0x{origin:08X} end=0x{origin + length:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
