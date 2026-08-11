from __future__ import annotations

import os
from pathlib import Path
import subprocess


QA_ROOT = Path(__file__).resolve().parents[3]
PRODUCT = Path(os.environ.get("EVSE_PRODUCT_DIR", "product/EVSE-Application")).resolve()
BUILD = QA_ROOT / "build" / "host-evse-relay"


def _run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        cwd=QA_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    print("$", " ".join(cmd))
    print(result.stdout)
    assert result.returncode == 0, result.stdout
    return result.stdout


def test_relay_driver_bench_safe_contract() -> None:
    """TC-EVSE-REL-U001 / SWE.4."""
    BUILD.mkdir(parents=True, exist_ok=True)
    exe = BUILD / "test_relay_driver"

    cmd = [
        "gcc",
        "-std=c11",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        "-I", str(QA_ROOT / "tests/host/evse/mocks"),
        "-I", str(PRODUCT / "MyApp/Common"),
        "-I", str(PRODUCT / "MyApp/Driver"),
        str(QA_ROOT / "tests/host/evse/test_relay_driver.c"),
        str(PRODUCT / "MyApp/Driver/relay.c"),
        "-o", str(exe),
    ]
    _run(cmd)
    out = _run([str(exe)])
    assert "RESULT=PASS TC-EVSE-REL-U001" in out


def test_hw_gpio_relay_active_level_mapping() -> None:
    """TC-EVSE-REL-U002 / SWE.4."""
    BUILD.mkdir(parents=True, exist_ok=True)
    exe = BUILD / "test_hw_gpio_relay"

    cmd = [
        "gcc",
        "-std=c11",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        "-I", str(QA_ROOT / "tests/host/evse/mocks"),
        "-I", str(PRODUCT / "MyApp/Common"),
        "-I", str(PRODUCT / "MyApp/Hardware"),
        str(QA_ROOT / "tests/host/evse/test_hw_gpio_relay.c"),
        str(PRODUCT / "MyApp/Hardware/hw_gpio.c"),
        "-o", str(exe),
    ]
    _run(cmd)
    out = _run([str(exe)])
    assert "RESULT=PASS TC-EVSE-REL-U002" in out