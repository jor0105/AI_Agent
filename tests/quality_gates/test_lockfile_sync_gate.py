"""Regression tests for staged lockfile validation."""

from __future__ import annotations

import subprocess
from pathlib import Path

import check_lockfile_sync as gate
import pytest
from git_changes import GitInspectionError, StagedChange, changed_records
from process_runner import ProcessLaunchError


def _git(root: Path, *args: str) -> None:
    """Run a successful Git command in an isolated test repository."""
    subprocess.run(
        ['git', *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


def _base_dependency_repository(root: Path) -> Path:
    """Create a committed uv project for dependency-metadata mutations."""
    _git(root, 'init')
    _git(root, 'config', 'user.email', 'quality@example.invalid')
    _git(root, 'config', 'user.name', 'Quality Gate')
    (root / 'pyproject.toml').write_text(
        "[project]\nname = 'demo'\nversion = '0.1.0'\n",
        encoding='utf-8',
    )
    (root / 'uv.lock').write_text('indexed lock\n', encoding='utf-8')
    _git(root, 'add', 'pyproject.toml', 'uv.lock')
    _git(root, 'commit', '-m', 'initial')
    return root


@pytest.fixture
def staged_lock_mismatch(tmp_path: Path) -> Path:
    """Create an index whose lock differs from its working-tree lock."""
    _base_dependency_repository(tmp_path)
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

    def test_statuses_preserve_rename_and_copy_updates(self) -> None:
        changes = [
            StagedChange('R100', 'uv.lock', 'poetry.lock'),
            StagedChange('C100', 'package.json', 'package-copy.json'),
        ]

        assert gate._status_by_path(changes) == {
            'uv.lock': 'R',
            'poetry.lock': 'R',
            'package.json': 'C',
            'package-copy.json': 'C',
        }
        assert gate._deleted_paths(changes) == {'uv.lock'}

    def test_native_checker_receives_the_staged_lockfile(
        self, staged_lock_mismatch: Path
    ) -> None:
        observed: list[str] = []

        def native_checker(
            manifest: Path, lockfile: str, snapshot: Path
        ) -> bool:
            del manifest
            observed.append((snapshot / lockfile).read_text(encoding='utf-8'))
            return False

        errors = gate.validate_staged_lockfiles(
            staged_lock_mismatch,
            changed_records(staged_lock_mismatch),
            native_checker,
        )

        assert observed == ['indexed lock\n']
        assert any('native read-only checker' in error for error in errors)

    def test_native_success_allows_a_manifest_without_lockfile_churn(
        self, staged_lock_mismatch: Path
    ) -> None:
        def native_checker(
            manifest: Path, lockfile: str, snapshot: Path
        ) -> bool:
            del manifest
            return (snapshot / lockfile).read_text(
                encoding='utf-8'
            ) == 'indexed lock\n'

        assert (
            gate.validate_staged_lockfiles(
                staged_lock_mismatch,
                changed_records(staged_lock_mismatch),
                native_checker,
            )
            == []
        )

    def test_native_success_allows_retiring_a_secondary_lockfile(
        self, staged_secondary_lock_deletion: Path
    ) -> None:
        def native_checker(
            manifest: Path, lockfile: str, snapshot: Path
        ) -> bool:
            del manifest
            return (
                lockfile == 'uv.lock'
                and (snapshot / lockfile).read_text(encoding='utf-8')
                == 'indexed uv lock\n'
            )

        assert (
            gate.validate_staged_lockfiles(
                staged_secondary_lock_deletion,
                changed_records(staged_secondary_lock_deletion),
                native_checker,
            )
            == []
        )

    @pytest.mark.parametrize('changed', ('manifest', 'lockfile', 'paired'))
    def test_native_coherence_accepts_each_relevant_change_shape(
        self, tmp_path: Path, changed: str
    ) -> None:
        root = _base_dependency_repository(tmp_path)
        if changed in {'manifest', 'paired'}:
            (root / 'pyproject.toml').write_text(
                "[project]\nname = 'demo'\nversion = '0.2.0'\n",
                encoding='utf-8',
            )
            _git(root, 'add', 'pyproject.toml')
        if changed in {'lockfile', 'paired'}:
            (root / 'uv.lock').write_text('updated lock\n', encoding='utf-8')
            _git(root, 'add', 'uv.lock')

        errors = gate.validate_staged_lockfiles(
            root,
            changed_records(root),
            lambda manifest, lockfile, snapshot: (
                manifest == Path('pyproject.toml')
                and lockfile == 'uv.lock'
                and (snapshot / lockfile).is_file()
            ),
        )

        assert errors == []

    @pytest.mark.parametrize(
        'operation', ('delete-manifest', 'rename-manifest')
    )
    def test_manifest_deletion_and_rename_away_fail(
        self, tmp_path: Path, operation: str
    ) -> None:
        root = _base_dependency_repository(tmp_path)
        if operation == 'delete-manifest':
            (root / 'pyproject.toml').unlink()
            _git(root, 'add', 'pyproject.toml')
        else:
            _git(root, 'mv', 'pyproject.toml', 'project.toml')

        errors = gate.validate_staged_lockfiles(
            root,
            changed_records(root),
            lambda manifest, lockfile, snapshot: True,
        )

        assert any('manifest deletion' in error for error in errors)

    @pytest.mark.parametrize('operation', ('delete-lock', 'rename-lock'))
    def test_required_lockfile_deletion_and_rename_away_fail(
        self, tmp_path: Path, operation: str
    ) -> None:
        root = _base_dependency_repository(tmp_path)
        if operation == 'delete-lock':
            (root / 'uv.lock').unlink()
            _git(root, 'add', 'uv.lock')
        else:
            _git(root, 'mv', 'uv.lock', 'renamed.lock')

        errors = gate.validate_staged_lockfiles(
            root,
            changed_records(root),
            lambda manifest, lockfile, snapshot: True,
        )

        assert any(
            'remains while deleting or renaming' in error for error in errors
        )

    def test_copy_metadata_retains_source_and_destination_semantics(
        self, tmp_path: Path
    ) -> None:
        root = _base_dependency_repository(tmp_path)
        (root / 'poetry.lock').write_bytes((root / 'uv.lock').read_bytes())
        _git(root, 'add', 'poetry.lock')
        records = changed_records(root)

        assert any(
            record.status.startswith('C')
            and record.old_path == 'uv.lock'
            and record.new_path == 'poetry.lock'
            for record in records
        )
        assert (
            gate.validate_staged_lockfiles(
                root,
                records,
                lambda manifest, lockfile, snapshot: lockfile == 'uv.lock',
            )
            == []
        )

    def test_incoherent_validation_does_not_modify_repository_files(
        self, staged_lock_mismatch: Path
    ) -> None:
        tracked = ('pyproject.toml', 'uv.lock')
        before = {
            path: (staged_lock_mismatch / path).read_bytes()
            for path in tracked
        }

        errors = gate.validate_staged_lockfiles(
            staged_lock_mismatch,
            changed_records(staged_lock_mismatch),
            lambda manifest, lockfile, snapshot: False,
        )

        assert errors
        assert before == {
            path: (staged_lock_mismatch / path).read_bytes()
            for path in tracked
        }

    def test_missing_native_tool_is_an_infrastructure_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def missing(*args: object, **kwargs: object) -> None:
            raise ProcessLaunchError('missing uv')

        monkeypatch.setattr(gate, 'run_process', missing)

        with pytest.raises(gate.NativeCheckError, match='could not execute'):
            gate._run_native_check(Path('pyproject.toml'), 'uv.lock', tmp_path)

    def test_git_inspection_failure_returns_error_status(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        def fail_root() -> Path:
            raise GitInspectionError('missing Git')

        monkeypatch.setattr(gate, 'repository_root', fail_root)

        assert gate.main() == 2
        assert 'ERROR [LOCKFILE]' in capsys.readouterr().err
