"""Subprocess boundary shared by local quality gates."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


class ProcessLaunchError(RuntimeError):
    """A requested process could not be started."""


@dataclass(frozen=True)
class ProcessResult:
    """Raw process result, including NUL-delimited byte output."""

    returncode: int
    stdout: bytes
    stderr: bytes


def run_process(
    args: Sequence[str | os.PathLike[str]],
    *,
    cwd: Path,
    input_bytes: bytes | None = None,
) -> ProcessResult:
    """Run explicit arguments without invoking a shell."""
    command = [os.fspath(argument) for argument in args]
    if not command:
        raise ProcessLaunchError('cannot launch an empty command.')
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            input=input_bytes,
            capture_output=True,
            check=False,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise ProcessLaunchError(
            f'could not start {command[0]!r}: {error}'
        ) from error
    return ProcessResult(result.returncode, result.stdout, result.stderr)
