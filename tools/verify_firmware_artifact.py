#!/usr/bin/env python3
"""Create CM evidence and independently validate an STM32 binary vector."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--elf", required=True, type=Path)
    parser.add_argument("--bin", required=True, type=Path)
    parser.add_argument("--flash-start", required=True, type=parse_int)
    parser.add_argument("--flash-end", required=True, type=parse_int)
    parser.add_argument("--max-size", required=True, type=parse_int)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    if not FULL_SHA.fullmatch(args.source_sha):
        raise SystemExit("source SHA must be a full lowercase 40-hex commit")
    if not args.elf.is_file() or not args.bin.is_file():
        raise SystemExit("ELF/BIN artifact is missing")
    binary = args.bin.read_bytes()
    if not 8 <= len(binary) <= args.max_size:
        raise SystemExit(f"BIN size {len(binary)} is outside 8..{args.max_size}")
    initial_msp = int.from_bytes(binary[0:4], "little")
    reset_handler = int.from_bytes(binary[4:8], "little")
    reset_address = reset_handler & ~1
    sram_valid = 0x20000000 <= initial_msp <= 0x20030000
    ccm_valid = 0x10000000 <= initial_msp <= 0x10010000
    if not (sram_valid or ccm_valid):
        raise SystemExit(f"invalid initial MSP 0x{initial_msp:08X}")
    if reset_handler & 1 == 0:
        raise SystemExit(f"reset handler is not Thumb 0x{reset_handler:08X}")
    if not args.flash_start <= reset_address < args.flash_end:
        raise SystemExit(f"reset handler 0x{reset_handler:08X} is outside target region")

    evidence = {
        "schema_version": 1,
        "generated_utc": datetime.now(UTC).isoformat(),
        "product": args.product,
        "source_sha": args.source_sha,
        "elf": {"path": args.elf.name, "sha256": sha256(args.elf), "size": args.elf.stat().st_size},
        "bin": {"path": args.bin.name, "sha256": sha256(args.bin), "size": len(binary)},
        "vector": {
            "initial_msp": f"0x{initial_msp:08X}",
            "reset_handler": f"0x{reset_handler:08X}",
            "region_start": f"0x{args.flash_start:08X}",
            "region_end": f"0x{args.flash_end:08X}",
        },
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"PASS artifact={args.product} sha256={evidence['bin']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
