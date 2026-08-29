"""Regression tests for the explicit subprocess boundary."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from process_runner import ProcessLaunchError, run_process


@pytest.mark.unit
def test_runner_preserves_nul_delimited_bytes(tmp_path: Path) -> None:
    result = run_process(
        [
            sys.executable,
            '-c',
            'import sys; data = sys.stdin.buffer.read(); '
            'sys.stdout.buffer.write(data); sys.stderr.buffer.write(b"err")',
        ],
        cwd=tmp_path,
        input_bytes=b'left\x00right\x00',
    )

    assert result.returncode == 0
    assert result.stdout == b'left\x00right\x00'
    assert result.stderr == b'err'


@pytest.mark.unit
def test_runner_keeps_tool_nonzero_distinct_from_launch_failure(
    tmp_path: Path,
) -> None:
    result = run_process(
        [sys.executable, '-c', 'raise SystemExit(7)'], cwd=tmp_path
    )

    assert result.returncode == 7

    with pytest.raises(ProcessLaunchError):
        run_process([str(tmp_path / 'missing-executable')], cwd=tmp_path)


@pytest.mark.unit
def test_runner_maps_invalid_argument_bytes_to_launch_failure(
    tmp_path: Path,
) -> None:
    with pytest.raises(ProcessLaunchError):
        run_process([sys.executable, 'bad\x00argument'], cwd=tmp_path)
