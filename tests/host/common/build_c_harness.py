from __future__ import annotations

import csv
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


class CBuildError(RuntimeError):
    pass


def compile_executable(
    *,
    output: Path,
    sources: list[Path],
    includes: list[Path],
    defines: list[str] | None = None,
) -> Path:
    compiler_parts = shlex.split(os.getenv("CC", "gcc"))
    if not compiler_parts or shutil.which(compiler_parts[0]) is None:
        raise CBuildError(f"C compiler is unavailable: {compiler_parts[0] if compiler_parts else ''}")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        *compiler_parts,
        "-std=c11",
        "-O0",
        "-g",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        *[f"-I{path}" for path in includes],
        *[f"-D{define}" for define in (defines or [])],
        *[str(path) for path in sources],
        "-o",
        str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise CBuildError(
            f"C harness compile failed ({completed.returncode})\n"
            f"command: {' '.join(command)}\n{completed.stdout}\n{completed.stderr}"
        )
    return output



# Provide a helper to get JIRA info
def get_jira_info(test_id: str):
    csv_path = Path(__file__).resolve().parent.parent.parent.parent / 'docs' / 'jira_export' / 'jira_export_issues.csv'
    if not csv_path.exists():
        return None, None
    try:
        with open(csv_path, encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and test_id in row[0]:
                    return row[1], row[0]
    except Exception:
        pass
    return None, None



def run_case(executable: Path, test_id: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [str(executable), test_id],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    if completed.returncode == 0:
        issue, summary = get_jira_info(test_id)
        if issue:
            print(f"\n✅ [PASS] {issue} : {summary} (Test ID: {test_id})", file=sys.stderr)
        else:
            print(f"\n✅ [PASS] (Test ID: {test_id})", file=sys.stderr)
    return completed
