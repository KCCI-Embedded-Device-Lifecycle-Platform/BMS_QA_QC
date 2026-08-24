"""Explicitly opt-in controllers for reset, bus fault, and power-loss injection."""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass


class FaultInjectionBlocked(RuntimeError):
    pass


@dataclass(slots=True)
class ExternalCommandController:
    command: str
    approval_environment: str
    timeout_s: float = 10.0

    def trigger(self) -> None:
        if os.getenv(self.approval_environment) != "YES":
            raise FaultInjectionBlocked(
                f"set {self.approval_environment}=YES only after bench safety approval"
            )
        if not self.command.strip():
            raise FaultInjectionBlocked("fault-injection command is not configured")
        completed = subprocess.run(
            shlex.split(self.command),
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout_s,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"fault-injection command failed rc={completed.returncode}: "
                f"{completed.stderr.strip()}"
            )
