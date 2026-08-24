from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.host
def test_reviewed_catalog_has_54_unique_traceable_cases() -> None:
    manifest = json.loads(
        (ROOT / "docs/jira_export/test_case_manifest.json").read_text(encoding="utf-8")
    )
    cases = manifest["cases"]
    assert manifest["test_count"] == 54 == len(cases)
    assert len({case["test_id"] for case in cases}) == 54
    for case in cases:
        assert case["requirement_id"].startswith("SWRS-")
        assert case["expected"]
        for reference in case["automation"].split(";"):
            assert (ROOT / reference).is_file(), f"{case['test_id']} missing {reference}"


@pytest.mark.host
def test_jira_csv_and_markdown_are_generated() -> None:
    assert (ROOT / "docs/jira_export/jira_test_cases.csv").stat().st_size > 1000
    text = (ROOT / "docs/jira_export/Jira_Test_Case_Catalog_IMPLEMENTED_FINAL.md").read_text(
        encoding="utf-8"
    )
    assert text.count("### TC-") == 54
    assert (ROOT / "docs/aspice/RTM.xlsx").stat().st_size > 10_000
