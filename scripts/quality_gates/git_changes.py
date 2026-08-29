"""Shared, fail-closed Git boundary for local quality gates."""

from __future__ import annotations

import os
import posixpath
import re
import tempfile
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from process_runner import ProcessLaunchError, ProcessResult, run_process

# fmt: off
EXTERNAL_HARNESS_ROOTS = ('.agents/', '.claude/', '.codex/', '.opencode/', '.github/prompts/')
PathArg = str | Path
PathArgs = Sequence[PathArg]


class GitInspectionError(RuntimeError):
    pass


class UnsafeRepositoryPathError(GitInspectionError, ValueError):
    pass


@dataclass(frozen=True)
class StagedChange:
    status: str
    old_path: str | None
    new_path: str | None


def _decode(data: bytes, description: str) -> str:
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError as error:
        raise GitInspectionError(f'{description} is not valid UTF-8.') from error


def run_git(args: Sequence[str], root: Path) -> ProcessResult:
    try:
        result = run_process(['git', *args], cwd=root)
    except ProcessLaunchError as error:
        raise GitInspectionError(str(error)) from error
    if result.returncode:
        detail = _decode(result.stderr or result.stdout, 'Git output').strip()
        raise GitInspectionError(detail or f'git {" ".join(args)} failed.')
    return result


def repository_root(root: Path | None = None) -> Path:
    value = _decode(
        run_git(['rev-parse', '--show-toplevel'], root or Path.cwd()).stdout,
        'Git repository root',
    ).strip()
    if not value:
        raise GitInspectionError('Git returned an invalid repository root.')
    return Path(value)


def normalize_path(path: str | Path) -> str:
    value = os.fspath(path).replace('\\', '/')
    if not value or '\x00' in value:
        raise UnsafeRepositoryPathError('repository paths must be non-empty.')
    if value.startswith('/') or PureWindowsPath(value).is_absolute():
        raise UnsafeRepositoryPathError(f'absolute repository path: {path!r}')
    if re.match(r'^[A-Za-z]:', value) or '..' in value.split('/'):
        raise UnsafeRepositoryPathError(f'unsafe repository path: {path!r}')
    normalized = posixpath.normpath(value)
    if normalized in {'', '..'} or normalized.startswith('../'):
        raise UnsafeRepositoryPathError(f'unsafe repository path: {path!r}')
    return normalized


def is_external_path(path: str | Path) -> bool:
    normalized = normalize_path(path)
    return any(
        normalized == root[:-1] or normalized.startswith(root)
        for root in EXTERNAL_HARNESS_ROOTS
    )


def _scope(value: str) -> bool:
    if value not in {'product', 'repository'}:
        raise GitInspectionError(f'unknown Git scope: {value!r}')
    return value == 'product'


def pathspecs(
    scope: str = 'product',
    paths: PathArgs = (),
) -> tuple[str, ...]:
    selected = tuple(normalize_path(path) for path in paths)
    product_scope = _scope(scope)
    if product_scope and any(is_external_path(path) for path in selected):
        raise UnsafeRepositoryPathError(
            'product-scoped Git operations cannot address external paths.'
        )
    targets = selected or ('.',)
    if not product_scope:
        return targets
    return (
        *targets,
        *(f':(exclude){root}**' for root in EXTERNAL_HARNESS_ROOTS),
    )


def verify_revision(revision: str, root: Path) -> str:
    if not revision or '\x00' in revision or revision.startswith('-'):
        raise GitInspectionError(f'invalid revision: {revision!r}')
    value = _decode(
        run_git(
            [
                'rev-parse',
                '--verify',
                '--end-of-options',
                f'{revision}^{{commit}}',
            ],
            root,
        ).stdout,
        'Git revision',
    ).strip()
    if not re.fullmatch(r'[0-9a-fA-F]{40}', value):
        raise GitInspectionError(f'Git returned an invalid commit: {value!r}')
    return value


def validated_revision_range(value: str, root: Path) -> tuple[str, str]:
    if value.count('...') != 1:
        raise GitInspectionError(
            'range must contain one BASE...HEAD separator.'
        )
    base, head = value.split('...')
    if not base or not head or any(character.isspace() for character in value):
        raise GitInspectionError(f'invalid revision range: {value!r}')
    return verify_revision(base, root), verify_revision(head, root)


def _nul_fields(data: bytes, description: str) -> list[str]:
    if not data:
        return []
    if not data.endswith(b'\0'):
        raise GitInspectionError(f'malformed NUL-delimited {description}.')
    fields = data[:-1].split(b'\0')
    if any(not field for field in fields):
        raise GitInspectionError(f'{description} contains an empty field.')
    return [normalize_path(_decode(field, description)) for field in fields]


def parse_name_status(data: bytes) -> list[StagedChange]:
    if not data:
        return []
    if not data.endswith(b'\0'):
        raise GitInspectionError('malformed NUL-delimited Git status output.')
    fields = iter(data[:-1].split(b'\0'))
    records: list[StagedChange] = []
    for raw_status in fields:
        status = _decode(raw_status, 'Git status')
        if not status:
            raise GitInspectionError('Git returned an empty status.')
        try:
            old_path = normalize_path(_decode(next(fields), 'Git path'))
            new_path = (
                normalize_path(_decode(next(fields), 'Git path'))
                if status[0] in {'R', 'C'}
                else None
            )
        except StopIteration as error:
            raise GitInspectionError('malformed Git name-status output.') from error
        records.append(
            StagedChange(status, old_path, new_path)
            if new_path is not None or status[0] == 'D'
            else StagedChange(status, None, old_path)
        )
    return records


def _relevant(record: StagedChange, product_scope: bool) -> bool:
    return not product_scope or any(
        path is not None and not is_external_path(path)
        for path in (record.old_path, record.new_path)
    )


def _diff_args(source: str | None, root: Path, revision: str | None, options: Sequence[str], product_scope: bool, paths: PathArgs) -> list[str]:
    if revision is not None:
        if source is not None:
            raise GitInspectionError('source and revision cannot be combined.')
        source = revision
    source_arg = (
        '--cached'
        if source is None
        else '...'.join(validated_revision_range(source, root))
    )
    return [
        'diff',
        source_arg,
        *options,
        '--',
        *pathspecs('product' if product_scope else 'repository', paths),
    ]


_DIFF_COMMON = ('-M', '-C', '--find-copies-harder')
_NAME_STATUS_OPTIONS = ('--name-status', '-z', *_DIFF_COMMON, '--no-ext-diff')
_DIFF_OPTIONS = ('--no-color', '--no-ext-diff', *_DIFF_COMMON)


def changed_records(root: Path, source: str | None = None, *, scope: str = 'product', paths: PathArgs = (), revision: str | None = None) -> list[StagedChange]:
    product_scope = _scope(scope)
    if product_scope:
        pathspecs('product', paths)
    result = run_git(
        _diff_args(
            source,
            root,
            revision,
            _NAME_STATUS_OPTIONS,
            False,
            paths,
        ),
        root,
    )
    return [
        record
        for record in parse_name_status(result.stdout)
        if _relevant(record, product_scope)
    ]


def changed_paths(root: Path, source: str | None = None, *, scope: str = 'product', paths: PathArgs = (), revision: str | None = None) -> list[str]:
    records = changed_records(
        root, source, scope=scope, paths=paths, revision=revision
    )
    return sorted({path for record in records for path in (record.old_path, record.new_path) if path is not None})


def unified_diff(root: Path, source: str | None = None, *, scope: str = 'product', paths: PathArgs = (), context: int = 0, revision: str | None = None) -> str:
    product_scope = _scope(scope)
    if product_scope:
        pathspecs('product', paths)
    result = run_git(
        _diff_args(
            source,
            root,
            revision,
            (*_DIFF_OPTIONS, f'-U{context}'),
            False,
            paths,
        ),
        root,
    )
    diff = _decode(result.stdout, 'Git unified diff')
    return diff if not product_scope else _filter_product_diff(diff)


def _section_paths(section: str) -> tuple[str, ...]:
    lines = section.splitlines()
    paths = [
        normalize_path(line[6:].split('\t', 1)[0])
        for line in lines
        if line.startswith(('--- a/', '+++ b/'))
    ]
    if paths:
        return tuple(dict.fromkeys(paths))
    if not lines or not lines[0].startswith('diff --git '):
        return ()
    match = re.match(r'^diff --git a/(.+) b/(.+)$', lines[0])
    if match is None:
        raise GitInspectionError('could not parse a Git diff file header.')
    return tuple(dict.fromkeys((normalize_path(match.group(1)), normalize_path(match.group(2)))))


def _filter_product_diff(diff: str) -> str:
    sections = re.split(r'(?=^diff --git )', diff, flags=re.MULTILINE)
    return ''.join(section for section in sections if section and any(not is_external_path(path) for path in _section_paths(section)))


def _path_list(args: Sequence[str], root: Path, product_scope: bool, paths: PathArgs) -> list[str]:
    values = _nul_fields(
        run_git(
            [
                *args,
                '--',
                *pathspecs(
                    'product' if product_scope else 'repository', paths
                ),
            ],
            root,
        ).stdout,
        'Git path output',
    )
    return sorted(
        {p for p in values if not product_scope or not is_external_path(p)}
    )


def indexed_paths(root: Path, *, scope: str = 'product', paths: PathArgs = ()) -> list[str]:
    product_scope = _scope(scope)
    args = ['ls-files', '--cached', '-z']
    return _path_list(args, root, product_scope, paths)


def revision_paths(root: Path, revision: str, *, scope: str = 'product', paths: PathArgs = ()) -> list[str]:
    product_scope = _scope(scope)
    if product_scope:
        pathspecs('product', paths)
    args = [
        'ls-tree', '-r', '-z', '--name-only', '--full-tree',
        verify_revision(revision, root),
    ]
    # ``ls-tree`` rejects exclude pathspec magic, so filter its safe path list
    # after the command while retaining path selection for repository scope.
    values = _path_list(args, root, False, paths)
    return sorted(
        {
            path
            for path in values
            if not product_scope or not is_external_path(path)
        }
    )


def read_text(path: PathArg, root: Path, revision: str | None = None, *, scope: str = 'product') -> str | None:
    normalized = normalize_path(path)
    if _scope(scope) and is_external_path(normalized):
        raise UnsafeRepositoryPathError(f'path is outside {scope}: {path!r}')
    data = _read_bytes(normalized, root, revision)
    label = (
        f'indexed {path}'
        if revision is None
        else f'revision {revision}:{path}'
    )
    return None if data is None else _decode(data, label)


def _read_bytes(path: str, root: Path, revision: str | None = None) -> bytes | None:
    resolved = None if revision is None else verify_revision(revision, root)
    args = (
        ['ls-files', '--cached', '-z']
        if resolved is None
        else ['ls-tree', '-r', '-z', '--name-only', '--full-tree', resolved]
    )
    description = 'Git index path output' if resolved is None else 'Git revision path output'
    listed = _nul_fields(
        run_git([*args, '--', path], root).stdout, description
    )
    if not listed:
        return None
    if listed != [path]:
        raise GitInspectionError(f'ambiguous Git object path for {path!r}.')
    prefix = ':' if resolved is None else f'{resolved}:'
    return run_git(['show', f'{prefix}{path}'], root).stdout


@contextmanager
def _materialize(paths: Sequence[str], reader: Callable[[str], bytes | None]) -> Iterator[Path]:
    try:
        with tempfile.TemporaryDirectory(
            prefix='quality-gate-snapshot-'
        ) as directory:
            snapshot_path = Path(directory)
            for path in paths:
                data = reader(path)
                if data is None:
                    raise GitInspectionError(
                        f'could not read snapshot path {path!r}.'
                    )
                target = snapshot_path / normalize_path(path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            yield snapshot_path
    except OSError as error:
        raise GitInspectionError(f'could not materialize the Git snapshot: {error}') from error


@contextmanager
def repository_snapshot(root: Path, revision: str | None = None, *, scope: str = 'product', paths: PathArgs = ()) -> Iterator[Path]:
    resolved = None if revision is None else verify_revision(revision, root)
    listed = (
        indexed_paths(root, scope=scope, paths=paths)
        if resolved is None
        else revision_paths(root, resolved, scope=scope, paths=paths)
    )
    with _materialize(
        listed, lambda path: _read_bytes(path, root, resolved)
    ) as snapshot_path:
        yield snapshot_path


# fmt: on
