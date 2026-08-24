#!/usr/bin/env python3
"""Run an approved HIL subset and persist configuration metadata.

The orchestrator never enables destructive tests by itself.  Environment gates
remain mandatory in the individual tests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--suite",
        choices=[
            "can",
            "can-infra",
            "can-start-stop",
            "can-fault",
            "can-link-fault",
            "safety",
            "ota",
            "all",
        ],
        default="all",
    )
    parser.add_argument("--reports", type=Path, default=Path("reports/hil"))
    parser.add_argument(
        "--allow-all-skipped",
        action="store_true",
        help="Permit a zero-execution diagnostic run; never use for formal qualification.",
    )
    parser.add_argument(
        "--require-all-executed",
        action="store_true",
        help="Fail a formal run when any selected HIL case is skipped.",
    )
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    args.reports.mkdir(parents=True, exist_ok=True)
    metadata = {
        "config_sha256": sha256(args.config),
        "platform": platform.platform(),
        "python": sys.version,
        "qa_commit": os.getenv("CI_COMMIT_SHA", "local"),
        "pipeline": os.getenv("CI_PIPELINE_URL", "local"),
        "product_baselines": config.get("product_baselines", {}),
    }
    (args.reports / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    selectors = {
        "can": ["hil/tests/test_can_timeout.py", "hil/tests/test_can_e2e.py", "hil/tests/test_can_bus_acceptance.py"],
        # Infrastructure acceptance deliberately has no ECU actuation.  It can
        # establish that the Pi analyzer sees the approved bus, but it cannot
        # claim a product-level safety PASS.
        "can-infra": [
            "hil/tests/test_can_bus_acceptance.py",
            "hil/tests/test_can_timeout.py::test_tc_can_hb_001_periodicity",
        ],
        "can-start-stop": [
            "hil/tests/test_can_e2e.py::test_tc_can_e2e_002_start_stop_state_sequence"
        ],
        "can-fault": [
            "hil/tests/test_can_e2e.py::test_tc_can_e2e_003_critical_fault_safe_off"
        ],
        "can-link-fault": [
            "hil/tests/test_can_timeout.py::test_tc_bms_link_001_timeout_and_recovery",
            "hil/tests/test_can_timeout.py::test_tc_evse_safe_004_bms_timeout_drives_pe11_low",
        ],
        "safety": ["hil/tests/test_safe_state.py", "hil/tests/test_bus_off_recovery.py"],
        "ota": [
            "hil/tests/test_ota_boot.py",
            "hil/tests/test_ota_crc_failure.py",
            "hil/tests/test_ota_update.py",
        ],
        "all": ["hil/tests"],
    }
    command = [
        sys.executable,
        "-m",
        "pytest",
        *selectors[args.suite],
        "-m",
        "hil",
        "--junitxml",
        str(args.reports / "junit.xml"),
    ]
    environment = os.environ.copy()
    environment["HIL_ENABLED"] = "1"
    environment["HIL_CONFIG"] = str(args.config.resolve())
    returncode = subprocess.run(command, env=environment, check=False).returncode
    if returncode != 0 or args.allow_all_skipped:
        return returncode

    junit_path = args.reports / "junit.xml"
    root = ET.parse(junit_path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)
    if tests == 0 or tests == skipped:
        print("BLOCKED_INFRA: HIL produced no executed test; all cases were skipped", file=sys.stderr)
        return 4
    if args.require_all_executed and skipped:
        print(
            f"BLOCKED_INFRA: formal HIL skipped {skipped}/{tests} selected cases",
            file=sys.stderr,
        )
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
