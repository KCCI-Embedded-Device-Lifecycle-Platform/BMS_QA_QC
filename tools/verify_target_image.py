#!/usr/bin/env python3
"""Use OpenOCD verify_image to bind a CI artifact to the connected target."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from hil.openocd_client import OpenOcdClient


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--target", required=True, choices=["bms", "evse", "ota"])
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-f]{40}", args.source_sha):
        raise SystemExit("source SHA must be full lowercase 40-hex")
    if not args.image.is_file():
        raise SystemExit(f"image does not exist: {args.image}")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    openocd = config.get("openocd", {})
    target_config = openocd.get(args.target)
    if target_config is None and args.target == "ota":
        target_config = openocd.get("evse")
    if not target_config:
        raise SystemExit(f"OpenOCD config is missing for {args.target}")

    with OpenOcdClient(
        host=str(target_config.get("host", "127.0.0.1")),
        port=int(target_config.get("port", 4444)),
        timeout_s=float(target_config.get("timeout_s", 10.0)),
    ) as client:
        client.command("halt")
        idcode = client.read_word(0xE0042000)
        output = client.command(f'verify_image "{args.image.resolve()}"')
        normalized = output.lower()
        if "verified" not in normalized or "error" in normalized or "failed" in normalized:
            raise SystemExit(f"OpenOCD image verification failed: {output}")
        # Resume only after the verification verdict and ID evidence are captured.
        client.command("resume")

    evidence = {
        "schema_version": 1,
        "generated_utc": datetime.now(UTC).isoformat(),
        "target": args.target,
        "target_idcode": f"0x{idcode:08X}",
        "source_sha": args.source_sha,
        "image": str(args.image),
        "image_sha256": sha256(args.image),
        "openocd_verify": output.strip(),
        "result": "PASS",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"PASS target={args.target} idcode=0x{idcode:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
