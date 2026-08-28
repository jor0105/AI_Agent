"""Git-index primitives shared by the local quality gates.

Every gate that decides whether a commit may proceed must inspect the Git
index, not a possibly divergent working tree.  This module centralizes that
boundary and materializes index snapshots only in temporary directories.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


class GitInspectionError(RuntimeError):
    """Raised when a quality gate cannot inspect the Git index."""


@dataclass(frozen=True)
class StagedChange:
    """A staged path change, retaining both sides of renames and copies."""

    status: str
    old_path: str | None
    new_path: str


def _run_git(
    args: Sequence[str], root: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run Git and convert operational failures into a fail-closed error."""
    try:
        result = subprocess.run(
            ['git', *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as err:
        raise GitInspectionError(str(err)) from err
    if result.returncode == 0:
        return result
    detail = result.stderr.strip() or result.stdout.strip()
    raise GitInspectionError(detail or f'git {" ".join(args)} failed')


def repository_root(root: Path | None = None) -> Path:
    """Return the root of the current Git working tree."""
    result = _run_git(['rev-parse', '--show-toplevel'], root)
    return Path(result.stdout.strip())


def normalize_path(path: str | Path) -> str:
    """Normalize a repository-relative path without consulting disk state."""
    value = str(path).replace('\\', '/')
    while value.startswith('./'):
        value = value[2:]
    return value


def index_file_exists(path: str | Path, root: Path) -> bool:
    """Return whether a path exists in the current Git index."""
    result = _run_git(
        ['ls-files', '--stage', '--', normalize_path(path)], root
    )
    return bool(result.stdout.strip())


def indexed_paths(root: Path) -> list[str]:
    """Return all paths currently present in the Git index."""
    result = _run_git(['ls-files', '--cached', '-z', '--'], root)
    return sorted(
        normalize_path(path) for path in result.stdout.split('\0') if path
    )


def read_index_text(path: str | Path, root: Path) -> str | None:
    """Read UTF-8 text from the index, or ``None`` when it is absent."""
    normalized = normalize_path(path)
    if not index_file_exists(normalized, root):
        return None
    return _run_git(['show', f':{normalized}'], root).stdout


def staged_diff(
    root: Path, paths: Sequence[str] = (), context: int = 0
) -> str:
    """Return a unified diff from the index for the selected paths."""
    args = ['diff', '--cached', '--no-color', f'-U{context}', '--']
    args.extend(normalize_path(path) for path in paths)
    return _run_git(args, root).stdout


def _parse_name_status(output: str) -> list[StagedChange]:
    """Parse Git's NUL-delimited name-status output conservatively."""
    fields = output.split('\0')
    changes: list[StagedChange] = []
    index = 0
    while index < len(fields) - 1:
        status = fields[index]
        index += 1
        if not status:
            continue
        kind = status[0]
        if kind in {'R', 'C'}:
            if index + 1 >= len(fields):
                raise GitInspectionError(
                    'malformed Git name-status output for rename or copy'
                )
            changes.append(
                StagedChange(
                    kind,
                    normalize_path(fields[index]),
                    normalize_path(fields[index + 1]),
                )
            )
            index += 2
            continue
        if index >= len(fields):
            raise GitInspectionError('malformed Git name-status output')
        changes.append(StagedChange(kind, None, normalize_path(fields[index])))
        index += 1
    return changes


def staged_changes(root: Path) -> list[StagedChange]:
    """Return all staged changes without discarding rename/copy metadata."""
    result = _run_git(
        ['diff', '--cached', '--name-status', '-z', '-M', '-C'], root
    )
    return _parse_name_status(result.stdout)


@contextmanager
def staged_snapshot(root: Path) -> Iterator[Path]:
    """Materialize the full Git index into an isolated temporary directory."""
    with tempfile.TemporaryDirectory(
        prefix='quality-gate-index-'
    ) as directory:
        snapshot = Path(directory)
        prefix = f'{snapshot}{os.sep}'
        _run_git(['checkout-index', '--all', f'--prefix={prefix}'], root)
        yield snapshot
