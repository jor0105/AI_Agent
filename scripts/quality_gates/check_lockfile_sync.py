"""Validate staged manifests and lockfiles without resolving dependencies."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from git_index import (
    GitInspectionError,
    StagedChange,
    index_file_exists,
    read_index_text,
    repository_root,
    staged_changes,
    staged_snapshot,
)

MANIFEST_LOCKFILES: dict[str, tuple[str, ...]] = {
    'package.json': (
        'pnpm-lock.yaml',
        'package-lock.json',
        'yarn.lock',
        'bun.lockb',
    ),
    'pyproject.toml': (
        'uv.lock',
        'poetry.lock',
        'requirements.txt',
        'Pipfile.lock',
    ),
    'requirements.in': ('requirements.txt', 'uv.lock', 'poetry.lock'),
    'Cargo.toml': ('Cargo.lock',),
    'go.mod': ('go.sum',),
    'composer.json': ('composer.lock',),
    'Gemfile': ('Gemfile.lock',),
}
NATIVE_COMMANDS: dict[tuple[str, str], tuple[str, ...]] = {
    ('pyproject.toml', 'uv.lock'): ('uv', 'lock', '--check'),
    ('pyproject.toml', 'poetry.lock'): ('poetry', 'check', '--lock'),
    ('Cargo.toml', 'Cargo.lock'): ('cargo', 'check', '--locked'),
}
DEPENDENCY_KEYS = (
    'dependencies',
    'devDependencies',
    'peerDependencies',
    'optionalDependencies',
    'bundleDependencies',
    'bundledDependencies',
)
LOCKFILE_UPDATED = frozenset({'A', 'M', 'R', 'C'})


class NativeCheckError(RuntimeError):
    """Raised when a native read-only lockfile checker cannot start."""


NativeRunner = Callable[[Path, str, Path], bool]


def _has_declared_dependencies(manifest: Path, root: Path) -> bool:
    """Return whether an indexed Node manifest declares dependencies."""
    if manifest.name != 'package.json':
        return True
    content = read_index_text(manifest, root)
    if content is None:
        return True
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return True
    if not isinstance(payload, dict):
        return True
    return any(bool(payload.get(key)) for key in DEPENDENCY_KEYS)


def _run_native_check(manifest: Path, lockfile: str, snapshot: Path) -> bool:
    """Run a native checker against the index snapshot only."""
    command = NATIVE_COMMANDS[(manifest.name, lockfile)]
    try:
        result = subprocess.run(
            command,
            cwd=snapshot / manifest.parent,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as err:
        command_text = ' '.join(command)
        raise NativeCheckError(
            f'could not execute {command_text!r} for {manifest}'
        ) from err
    return result.returncode == 0


def _status_by_path(changes: list[StagedChange]) -> dict[str, str]:
    """Return the effective staged status for each new path."""
    return {change.new_path: change.status for change in changes}


def _validate_manifest(
    manifest: Path,
    root: Path,
    snapshot: Path,
    statuses: dict[str, str],
    native_runner: NativeRunner,
) -> list[str]:
    """Validate one staged manifest against the same staged snapshot."""
    if manifest.parent != Path():
        return [
            f'{manifest}: child manifests require an explicit workspace '
            'validator; refusing to infer a shared root lockfile.'
        ]
    if not index_file_exists(manifest, root):
        return [
            f'{manifest}: manifest deletion is not supported by this gate.'
        ]
    if not _has_declared_dependencies(manifest, root):
        return []

    candidates = MANIFEST_LOCKFILES[manifest.name]
    existing = [
        lockfile
        for lockfile in candidates
        if index_file_exists(lockfile, root)
    ]
    if not existing:
        return [
            f'{manifest}: no supported lockfile exists in the Git index '
            f'({", ".join(candidates)}).'
        ]

    native_lockfiles = [
        lockfile
        for lockfile in existing
        if (manifest.name, lockfile) in NATIVE_COMMANDS
    ]
    if native_lockfiles:
        if any(
            native_runner(manifest, lockfile, snapshot)
            for lockfile in native_lockfiles
        ):
            return []
        return [
            f'{manifest}: staged lockfile is not coherent according to its '
            'native read-only checker.'
        ]

    deleted = [
        lockfile for lockfile in candidates if statuses.get(lockfile) == 'D'
    ]
    if deleted:
        return [
            f'{manifest}: manifest changed while deleting lockfile(s): '
            f'{", ".join(deleted)}.'
        ]

    if any(
        statuses.get(lockfile) in LOCKFILE_UPDATED for lockfile in existing
    ):
        return []
    return [
        f'{manifest}: manifest changed without an updated local lockfile '
        f'({", ".join(existing)}).'
    ]


def validate_staged_lockfiles(
    root: Path,
    changes: list[StagedChange],
    native_runner: NativeRunner = _run_native_check,
) -> list[str]:
    """Validate every staged manifest without reading the working tree."""
    manifests = [
        Path(change.new_path)
        for change in changes
        if Path(change.new_path).name in MANIFEST_LOCKFILES
    ]
    if not manifests:
        return []
    statuses = _status_by_path(changes)
    with staged_snapshot(root) as snapshot:
        errors: list[str] = []
        for manifest in manifests:
            errors.extend(
                _validate_manifest(
                    manifest,
                    root,
                    snapshot,
                    statuses,
                    native_runner,
                )
            )
    return errors


def main() -> int:
    """Run the staged lockfile gate and return its documented status code."""
    try:
        root = repository_root()
        changes = staged_changes(root)
        errors = validate_staged_lockfiles(root, changes)
    except (GitInspectionError, NativeCheckError) as err:
        print(f'ERROR [LOCKFILE]: {err}', file=sys.stderr)
        return 2

    if not any(
        Path(change.new_path).name in MANIFEST_LOCKFILES for change in changes
    ):
        print('SKIP [LOCKFILE]: No staged manifest files to inspect.')
        return 0
    if errors:
        print(
            'FAIL [LOCKFILE]: Staged dependency metadata is invalid:',
            file=sys.stderr,
        )
        for error in errors:
            print(f'  • {error}', file=sys.stderr)
        print(
            'Resolution: update dependencies deliberately, stage the resulting '
            'lockfile, and retry the commit.',
            file=sys.stderr,
        )
        return 1
    print('PASS [LOCKFILE]: Staged dependency metadata is coherent.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
