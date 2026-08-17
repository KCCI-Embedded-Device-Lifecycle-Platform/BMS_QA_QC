from __future__ import annotations

import os
import shlex
import shutil
import subprocess
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


def run_case(executable: Path, test_id: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(executable), test_id],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
