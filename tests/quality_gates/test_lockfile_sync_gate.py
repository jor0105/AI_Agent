"""Regression tests for staged lockfile validation."""

from __future__ import annotations

import subprocess
from pathlib import Path

import check_lockfile_sync as gate
import pytest
from git_index import staged_changes


def _git(root: Path, *args: str) -> None:
    """Run a successful Git command in an isolated test repository."""
    subprocess.run(
        ['git', *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture
def staged_lock_mismatch(tmp_path: Path) -> Path:
    """Create an index whose lock differs from its working-tree lock."""
    _git(tmp_path, 'init')
    _git(tmp_path, 'config', 'user.email', 'quality@example.invalid')
    _git(tmp_path, 'config', 'user.name', 'Quality Gate')
    (tmp_path / 'pyproject.toml').write_text(
        "[project]\nname = 'demo'\nversion = '0.1.0'\n",
        encoding='utf-8',
    )
    (tmp_path / 'uv.lock').write_text('indexed lock\n', encoding='utf-8')
    _git(tmp_path, 'add', 'pyproject.toml', 'uv.lock')
    _git(tmp_path, 'commit', '-m', 'initial')
    (tmp_path / 'pyproject.toml').write_text(
        "[project]\nname = 'demo'\nversion = '0.2.0'\n",
        encoding='utf-8',
    )
    _git(tmp_path, 'add', 'pyproject.toml')
    (tmp_path / 'uv.lock').write_text('working tree lock\n', encoding='utf-8')
    return tmp_path


@pytest.fixture
def staged_secondary_lock_deletion(tmp_path: Path) -> Path:
    """Stage removal of a secondary lock while retaining the uv lock."""
    _git(tmp_path, 'init')
    _git(tmp_path, 'config', 'user.email', 'quality@example.invalid')
    _git(tmp_path, 'config', 'user.name', 'Quality Gate')
    (tmp_path / 'pyproject.toml').write_text(
        "[project]\nname = 'demo'\nversion = '0.1.0'\n",
        encoding='utf-8',
    )
    (tmp_path / 'uv.lock').write_text('indexed uv lock\n', encoding='utf-8')
    (tmp_path / 'poetry.lock').write_text(
        'indexed poetry lock\n', encoding='utf-8'
    )
    _git(tmp_path, 'add', 'pyproject.toml', 'uv.lock', 'poetry.lock')
    _git(tmp_path, 'commit', '-m', 'initial')
    (tmp_path / 'pyproject.toml').write_text(
        "[project]\nname = 'demo'\nversion = '0.2.0'\n",
        encoding='utf-8',
    )
    (tmp_path / 'poetry.lock').unlink()
    _git(tmp_path, 'add', 'pyproject.toml', 'poetry.lock')
    return tmp_path


@pytest.mark.unit
class TestStagedLockfileSync:
    """Native validation must receive the index snapshot, never the worktree."""

    def test_native_checker_receives_the_staged_lockfile(
        self, staged_lock_mismatch
    ):
        observed: list[str] = []

        def native_checker(manifest, lockfile, snapshot):
            observed.append((snapshot / lockfile).read_text(encoding='utf-8'))
            return False

        errors = gate.validate_staged_lockfiles(
            staged_lock_mismatch,
            staged_changes(staged_lock_mismatch),
            native_checker,
        )

        assert observed == ['indexed lock\n']
        assert any('native read-only checker' in error for error in errors)

    def test_native_success_allows_a_manifest_without_lockfile_churn(
        self, staged_lock_mismatch
    ):
        def native_checker(manifest, lockfile, snapshot):
            return (snapshot / lockfile).read_text(
                encoding='utf-8'
            ) == 'indexed lock\n'

        assert (
            gate.validate_staged_lockfiles(
                staged_lock_mismatch,
                staged_changes(staged_lock_mismatch),
                native_checker,
            )
            == []
        )

    def test_native_success_allows_retiring_a_secondary_lockfile(
        self, staged_secondary_lock_deletion
    ):
        def native_checker(manifest, lockfile, snapshot):
            return (
                lockfile == 'uv.lock'
                and (snapshot / lockfile).read_text(encoding='utf-8')
                == 'indexed uv lock\n'
            )

        assert (
            gate.validate_staged_lockfiles(
                staged_secondary_lock_deletion,
                staged_changes(staged_secondary_lock_deletion),
                native_checker,
            )
            == []
        )
