"""Standalone JUnit writer for non-pytest orchestration results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


@dataclass(slots=True)
class CaseResult:
    test_id: str
    elapsed_s: float
    status: str
    message: str = ""
    evidence: str = ""


def write_junit(path: str | Path, suite_name: str, results: list[CaseResult]) -> None:
    failure_statuses = {"FAIL_PRODUCT", "FAIL_TEST", "MISMATCH_CONFIGURATION"}
    skipped_statuses = {
        "GAP_REQUIREMENT",
        "BLOCKED_INFRA",
        "NOT_APPLICABLE",
    }
    allowed = {"PASS", *failure_statuses, *skipped_statuses}
    invalid = [result.status for result in results if result.status not in allowed]
    if invalid:
        raise ValueError(f"unsupported QA result classification: {invalid}")
    failures = sum(result.status in failure_statuses for result in results)
    skipped = sum(result.status in skipped_statuses for result in results)
    suite = ET.Element(
        "testsuite",
        name=suite_name,
        tests=str(len(results)),
        failures=str(failures),
        skipped=str(skipped),
        time=f"{sum(result.elapsed_s for result in results):.6f}",
    )
    for result in results:
        case = ET.SubElement(
            suite,
            "testcase",
            classname=suite_name,
            name=result.test_id,
            time=f"{result.elapsed_s:.6f}",
        )
        if result.status in failure_statuses:
            ET.SubElement(case, "failure", message=result.message).text = result.evidence
        elif result.status in skipped_statuses:
            ET.SubElement(case, "skipped", message=result.message)
        if result.evidence:
            ET.SubElement(case, "system-out").text = result.evidence
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(suite)
    ET.ElementTree(suite).write(output, encoding="utf-8", xml_declaration=True)
