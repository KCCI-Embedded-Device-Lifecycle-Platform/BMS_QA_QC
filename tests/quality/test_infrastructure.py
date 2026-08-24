from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from hil.report_junit import CaseResult, write_junit

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.host
def test_tc_infra_cm_001(tmp_path: Path) -> None:
    baseline = json.loads((ROOT / "config/product-baseline.json").read_text(encoding="utf-8"))
    for product in baseline["products"].values():
        ref = product["candidate_ref"]
        assert len(ref) == 40 and all(character in "0123456789abcdef" for character in ref)

    binary = tmp_path / "image.bin"
    elf = tmp_path / "image.elf"
    manifest = tmp_path / "manifest.json"
    binary.write_bytes(
        (0x20001000).to_bytes(4, "little")
        + (0x08020009).to_bytes(4, "little")
        + b"QA-EVIDENCE"
    )
    elf.write_bytes(b"ELF-QA-EVIDENCE")
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/verify_firmware_artifact.py"),
            "--product",
            "self-test",
            "--source-sha",
            "a" * 40,
            "--elf",
            str(elf),
            "--bin",
            str(binary),
            "--flash-start",
            "0x08020000",
            "--flash-end",
            "0x08100000",
            "--max-size",
            "0xE0000",
            "--manifest",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(manifest.read_text(encoding="utf-8"))["source_sha"] == "a" * 40

    linker_file = tmp_path / "STM32F429xx_FLASH.ld"
    linker_file.write_text(
        "MEMORY\n{\n  FLASH (rx) : ORIGIN = 0x08020000, LENGTH = 896K\n}\n",
        encoding="utf-8",
    )
    completed_linker = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/check_linker_layout.py"),
            "--linker",
            str(tmp_path / "STM32F429XX_FLASH.ld"),
            "--origin",
            "0x08020000",
            "--end",
            "0x08100000",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed_linker.returncode == 0, completed_linker.stdout + completed_linker.stderr


@pytest.mark.host
def test_tc_infra_pipe_001() -> None:
    ci_text = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    core_text = (ROOT / "ci/qa-core.yml").read_text(encoding="utf-8")
    assert "ci/qa-core.yml" in ci_text
    assert "qa_host_tests:" in core_text
    assert "qa_hil_can_infra:" in core_text
    assert "qa_hil_can_start_stop:" in core_text
    assert "qa_hil_safety:" in core_text


@pytest.mark.host
def test_tc_infra_res_001() -> None:
    allowed = {
        "PASS",
        "FAIL_PRODUCT",
        "GAP_REQUIREMENT",
        "FAIL_TEST",
        "BLOCKED_INFRA",
        "MISMATCH_CONFIGURATION",
        "NOT_APPLICABLE",
    }
    schema = json.loads((ROOT / "docs/aspice/result-schema.json").read_text(encoding="utf-8"))
    assert set(schema["allowed_classifications"]) == allowed


@pytest.mark.host
def test_tc_infra_junit_001(tmp_path: Path) -> None:
    output = tmp_path / "junit.xml"
    write_junit(
        output,
        "qa-self-test",
        [
            CaseResult("PASS-CASE", 0.1, "PASS", evidence="sha=abc"),
            CaseResult("FAIL-CASE", 0.2, "FAIL_TEST", message="oracle mismatch"),
            CaseResult(
                "GAP-CASE", 0.0, "GAP_REQUIREMENT", message="requirement gap"
            ),
        ],
    )
    suite = ET.parse(output).getroot()
    assert suite.attrib["tests"] == "3"
    assert suite.attrib["failures"] == "1"
    assert suite.attrib["skipped"] == "1"


@pytest.mark.host
def test_tc_ota_gate_001() -> None:
    ci_text = (ROOT / "ci/qa-core.yml").read_text(encoding="utf-8")
    job = ci_text.split("qa_hil_ota_update:", 1)[1]
    assert 'HIL_ALLOW_OTA_ERASE' in job
    assert "when: manual" in job
    assert 'CI_COMMIT_REF_PROTECTED == "true"' in job
