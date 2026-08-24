from __future__ import annotations

import os
from pathlib import Path

QA_ROOT = Path(__file__).resolve().parents[3]


def _resolve_product(environment: str, sibling: str) -> Path:
    configured = os.getenv(environment)
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend([QA_ROOT / ".products" / sibling, QA_ROOT.parent / sibling])
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    raise FileNotFoundError(
        f"{environment} is not configured and product checkout {sibling!r} was not found"
    )


def bms_product_dir() -> Path:
    return _resolve_product("BMS_PRODUCT_DIR", "BMS")


def evse_product_dir() -> Path:
    return _resolve_product("EVSE_PRODUCT_DIR", "EVSE-Application")


def ota_boot_dir() -> Path:
    configured = os.getenv("OTA_BOOT_DIR")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        [
            QA_ROOT / ".products" / "ota-platform" / "EVSE_BOOT",
            QA_ROOT.parent / "ota-platform" / "EVSE_BOOT",
        ]
    )
    for candidate in candidates:
        direct = candidate / "App" / "ap_boot_update.c"
        nested = candidate / "EVSE_BOOT" / "App" / "ap_boot_update.c"
        if direct.is_file():
            return candidate.resolve()
        if nested.is_file():
            return (candidate / "EVSE_BOOT").resolve()
    raise FileNotFoundError("OTA_BOOT_DIR/canonical ota-platform EVSE_BOOT checkout not found")
