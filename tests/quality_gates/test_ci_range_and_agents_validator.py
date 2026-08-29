"""Regression tests for CI range selection and strict AGENTS validation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from resolve_ci_range import CIRangeError, resolve_range

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ['git', *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


def _repository_with_two_commits(tmp_path: Path) -> Path:
    _git(tmp_path, 'init')
    _git(tmp_path, 'config', 'user.email', 'quality@example.invalid')
    _git(tmp_path, 'config', 'user.name', 'Quality Gate')
    target = tmp_path / 'tracked.txt'
    target.write_text('one\n', encoding='utf-8')
    _git(tmp_path, 'add', '--', 'tracked.txt')
    _git(tmp_path, 'commit', '-m', 'initial')
    target.write_text('two\n', encoding='utf-8')
    _git(tmp_path, 'add', '--', 'tracked.txt')
    _git(tmp_path, 'commit', '-m', 'second')
    return tmp_path


@pytest.mark.unit
def test_resolver_uses_exact_pull_request_shas(tmp_path: Path) -> None:
    root = _repository_with_two_commits(tmp_path)
    base = _git(root, 'rev-parse', 'HEAD^').stdout.strip()
    head = _git(root, 'rev-parse', 'HEAD').stdout.strip()
    event = root / 'event.json'
    event.write_text(
        json.dumps(
            {'pull_request': {'base': {'sha': base}, 'head': {'sha': head}}}
        ),
        encoding='utf-8',
    )

    assert resolve_range('pull_request', event, None, None, root) == (
        f'{base}...{head}'
    )


@pytest.mark.unit
def test_resolver_uses_push_range_and_dispatch_fallback(
    tmp_path: Path,
) -> None:
    root = _repository_with_two_commits(tmp_path)
    base = _git(root, 'rev-parse', 'HEAD^').stdout.strip()
    head = _git(root, 'rev-parse', 'HEAD').stdout.strip()

    assert resolve_range('push', None, base, head, root) == f'{base}...{head}'
    assert resolve_range('workflow_dispatch', None, None, None, root) == (
        f'{base}...{head}'
    )
    assert resolve_range('push', None, '0' * 40, head, root) == (
        f'{base}...{head}'
    )


@pytest.mark.unit
def test_resolver_reads_push_before_from_event_payload(tmp_path: Path) -> None:
    root = _repository_with_two_commits(tmp_path)
    base = _git(root, 'rev-parse', 'HEAD^').stdout.strip()
    head = _git(root, 'rev-parse', 'HEAD').stdout.strip()
    event = root / 'event.json'
    event.write_text(json.dumps({'before': base}), encoding='utf-8')

    assert resolve_range('push', event, None, head, root) == (
        f'{base}...{head}'
    )


@pytest.mark.unit
def test_resolver_falls_back_for_an_all_zero_push_payload(
    tmp_path: Path,
) -> None:
    root = _repository_with_two_commits(tmp_path)
    base = _git(root, 'rev-parse', 'HEAD^').stdout.strip()
    head = _git(root, 'rev-parse', 'HEAD').stdout.strip()
    event = root / 'event.json'
    event.write_text(json.dumps({'before': '0' * 40}), encoding='utf-8')

    assert resolve_range('push', event, None, head, root) == (
        f'{base}...{head}'
    )


@pytest.mark.unit
def test_resolver_rejects_incomplete_explicit_ranges(tmp_path: Path) -> None:
    root = _repository_with_two_commits(tmp_path)

    with pytest.raises(CIRangeError):
        resolve_range(None, None, None, None, root, base='HEAD')


@pytest.mark.unit
def test_strict_agents_validator_rejects_an_invalid_temp_document(
    tmp_path: Path,
) -> None:
    validator = (
        REPOSITORY_ROOT
        / '.agents'
        / 'skills'
        / 'agents-md-author'
        / 'scripts'
        / 'validate_agents_md.py'
    )
    invalid = tmp_path / 'AGENTS.md'
    invalid.write_text('# AGENTS.md\n\nStatus: Draft\n', encoding='utf-8')

    result = subprocess.run(
        [
            sys.executable,
            str(validator),
            '--file',
            str(invalid),
            '--strict-governance',
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0


@pytest.mark.unit
def test_repository_agents_document_passes_strict_validator() -> None:
    validator = (
        REPOSITORY_ROOT
        / '.agents'
        / 'skills'
        / 'agents-md-author'
        / 'scripts'
        / 'validate_agents_md.py'
    )
    result = subprocess.run(
        [
            sys.executable,
            str(validator),
            '--file',
            str(REPOSITORY_ROOT / 'AGENTS.md'),
            '--strict-governance',
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
