#!/usr/bin/env python3
"""Fail CI when a FLASH linker region overlaps an approved reserved region."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FLASH = re.compile(
    r"FLASH\s*\([^)]*\)\s*:\s*ORIGIN\s*=\s*(0x[0-9A-Fa-f]+)\s*,\s*LENGTH\s*=\s*([0-9]+)([KkMm]?)"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--linker", required=True, type=Path)
    parser.add_argument("--origin", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--end", required=True, type=lambda value: int(value, 0))
    args = parser.parse_args()

    text = args.linker.read_text(encoding="utf-8", errors="replace")
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
    print(f"PASS linker origin=0x{origin:08X} end=0x{origin + length:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
