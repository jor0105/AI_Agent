"""Validate staged manifests and lockfiles without resolving dependencies."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path

from git_changes import (
    GitInspectionError,
    StagedChange,
    changed_records,
    read_text,
    repository_root,
    repository_snapshot,
)
from process_runner import ProcessLaunchError, run_process

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
MANIFEST_LOCKFILE_REQUIRED = {'pyproject.toml': 'uv.lock'}


class NativeCheckError(RuntimeError):
    """Raised when a native read-only lockfile checker cannot start."""


NativeRunner = Callable[[Path, str, Path], bool]


def _has_declared_dependencies(manifest: Path, root: Path) -> bool:
    """Return whether an indexed Node manifest declares dependencies."""
    if manifest.name != 'package.json':
        return True
    content = read_text(manifest, root)
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
        result = run_process(command, cwd=snapshot / manifest.parent)
    except ProcessLaunchError as err:
        command_text = ' '.join(command)
        raise NativeCheckError(
            f'could not execute {command_text!r} for {manifest}'
        ) from err
    return result.returncode == 0


def _status_by_path(changes: list[StagedChange]) -> dict[str, str]:
    """Return the effective staged status for every represented path."""
    statuses: dict[str, str] = {}
    for change in changes:
        status = change.status[:1]
        if change.old_path is not None:
            statuses[change.old_path] = (
                'D' if change.new_path is None else status
            )
        if change.new_path is not None:
            statuses[change.new_path] = status
    return statuses


def _changed_paths(changes: list[StagedChange]) -> set[str]:
    return {
        path
        for change in changes
        for path in (change.old_path, change.new_path)
        if path is not None
    }


def _deleted_paths(changes: list[StagedChange]) -> set[str]:
    return {
        change.old_path
        for change in changes
        if change.old_path is not None
        and (
            change.status.startswith('D')
            or (
                change.status.startswith('R')
                and change.old_path != change.new_path
            )
        )
    }


def _changed_manifest_paths(
    changes: list[StagedChange], root: Path
) -> set[Path]:
    changed = _changed_paths(changes)
    manifests: set[Path] = set()
    for path in changed:
        path_object = Path(path)
        name = path_object.name
        if name in MANIFEST_LOCKFILES:
            manifests.add(path_object)
            continue
        for manifest_name, lockfiles in MANIFEST_LOCKFILES.items():
            if name != manifest_name and name not in lockfiles:
                continue
            candidate = path_object.with_name(manifest_name)
            if (
                candidate.as_posix() in changed
                or read_text(candidate, root) is not None
            ):
                manifests.add(candidate)
    return manifests


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
    if read_text(manifest, root) is None:
        return [
            f'{manifest}: manifest deletion is not supported by this gate.'
        ]
    if not _has_declared_dependencies(manifest, root):
        return []

    candidates = MANIFEST_LOCKFILES[manifest.name]
    existing = [
        lockfile
        for lockfile in candidates
        if read_text(lockfile, root) is not None
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

    required_lockfile = MANIFEST_LOCKFILE_REQUIRED.get(manifest.name)
    deleted = (
        [required_lockfile]
        if required_lockfile is not None
        and statuses.get(required_lockfile) == 'D'
        else []
    )
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
    manifests = sorted(_changed_manifest_paths(changes, root))
    if not manifests:
        return []
    statuses = _status_by_path(changes)
    deleted_paths = _deleted_paths(changes)
    with repository_snapshot(root) as snapshot:
        errors: list[str] = []
        for manifest in manifests:
            required_lockfile = MANIFEST_LOCKFILE_REQUIRED.get(manifest.name)
            deleted_locks = (
                [required_lockfile]
                if required_lockfile is not None
                and required_lockfile in deleted_paths
                else []
            )
            if deleted_locks and read_text(manifest, root) is not None:
                errors.append(
                    f'{manifest}: manifest remains while deleting or renaming '
                    f'lockfile(s): {", ".join(deleted_locks)}.'
                )
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
        changes = changed_records(root)
        changed_paths = _changed_paths(changes)
        supported_names = set(MANIFEST_LOCKFILES) | {
            lockfile
            for lockfiles in MANIFEST_LOCKFILES.values()
            for lockfile in lockfiles
        }
        relevant = any(
            Path(path).name in supported_names for path in changed_paths
        )
        errors = validate_staged_lockfiles(root, changes)
    except (GitInspectionError, NativeCheckError) as err:
        print(f'ERROR [LOCKFILE]: {err}', file=sys.stderr)
        return 2

    if not relevant:
        print('SKIP [LOCKFILE]: No staged manifest files to inspect.')
        return 0
    if not _changed_manifest_paths(changes, root) and not errors:
        errors = [
            'changed dependency metadata has no manifest in the Git index.'
        ]
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
