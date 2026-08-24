from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from hil.can_adapter import CanAdapter, create_can_adapter


@pytest.fixture(scope="session")
def hil_config() -> dict[str, Any]:
    if os.getenv("HIL_ENABLED") != "1":
        pytest.skip("BLOCKED_INFRA: set HIL_ENABLED=1 on the approved Raspberry Pi runner")
    path_value = os.getenv("HIL_CONFIG")
    if not path_value:
        pytest.fail("BLOCKED_INFRA: HIL_CONFIG is not set")
    path = Path(path_value)
    if not path.is_file():
        pytest.fail(f"BLOCKED_INFRA: HIL_CONFIG does not exist: {path}")
    config = json.loads(path.read_text(encoding="utf-8"))
    if os.getenv("HIL_FORMAL") == "1":
        fixture = config.get("fixture", {})
        if fixture.get("hard_interlock_confirmed") is not True:
            pytest.fail(
                "BLOCKED_INFRA: formal HIL requires fixture.hard_interlock_confirmed=true"
            )
        baselines = config.get("product_baselines", {})
        if not baselines or any(len(str(value)) != 40 for value in baselines.values()):
            pytest.fail("MISMATCH_CONFIGURATION: formal HIL requires full product SHAs")
    return config


@pytest.fixture
def can_adapter(hil_config: dict[str, Any]) -> CanAdapter:
    adapter = create_can_adapter(hil_config["can"])
    try:
        yield adapter
    finally:
        adapter.close()
