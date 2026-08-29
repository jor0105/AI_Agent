"""Regression tests for the shared staged and revision Git boundary."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from git_changes import (
    EXTERNAL_HARNESS_ROOTS,
    GitInspectionError,
    UnsafeRepositoryPathError,
    changed_paths,
    changed_records,
    indexed_paths,
    normalize_path,
    parse_name_status,
    pathspecs,
    read_text,
    repository_root,
    repository_snapshot,
    revision_paths,
    unified_diff,
    verify_revision,
)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ['git', *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


def _new_repository(tmp_path: Path) -> Path:
    _git(tmp_path, 'init')
    _git(tmp_path, 'config', 'user.email', 'quality@example.invalid')
    _git(tmp_path, 'config', 'user.name', 'Quality Gate')
    product = tmp_path / 'src' / 'product.py'
    product.parent.mkdir(parents=True)
    product.write_text('value = 1\n', encoding='utf-8')
    for root in EXTERNAL_HARNESS_ROOTS:
        path = tmp_path / root / 'fixture.txt'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('external\n', encoding='utf-8')
    _git(tmp_path, 'add', '--', '.')
    _git(tmp_path, 'commit', '-m', 'initial')
    return tmp_path


@pytest.mark.unit
class TestGitChanges:
    """The common boundary must preserve context and fail closed."""

    def test_normalizes_safe_paths_and_rejects_unsafe_paths(self) -> None:
        assert normalize_path('././src\\product.py') == 'src/product.py'
        assert normalize_path('.agents/fixture.txt') == '.agents/fixture.txt'
        for path in (
            '/tmp/file.py',
            '../file.py',
            'src/../file.py',
            'C:/file.py',
        ):
            with pytest.raises(UnsafeRepositoryPathError):
                normalize_path(path)

    def test_product_pathspecs_keep_all_external_exclusions(self) -> None:
        specs = pathspecs('product', ('src/product.py',))

        assert specs[0] == 'src/product.py'
        assert specs[1:] == tuple(
            f':(exclude){root}**' for root in EXTERNAL_HARNESS_ROOTS
        )

    def test_product_scope_filters_external_only_changes(
        self, tmp_path: Path
    ) -> None:
        root = _new_repository(tmp_path)
        (root / 'src' / 'product.py').write_text(
            'value = 2\n', encoding='utf-8'
        )
        external_paths = [
            f'{external_root}fixture.txt'
            for external_root in EXTERNAL_HARNESS_ROOTS
        ]
        for external_path in external_paths:
            (root / external_path).write_text('changed\n', encoding='utf-8')
        _git(root, 'add', '--', 'src/product.py', *external_paths)

        product_records = changed_records(root)

        assert any(
            record.new_path == 'src/product.py' for record in product_records
        )
        assert all(
            path is None
            or not any(
                path.startswith(root) for root in EXTERNAL_HARNESS_ROOTS
            )
            for record in product_records
            for path in (record.old_path, record.new_path)
        )
        repository_paths = changed_paths(root, scope='repository')
        assert all(path in repository_paths for path in external_paths)
        assert 'src/product.py' in changed_paths(root)
        assert all(path not in changed_paths(root) for path in external_paths)

    def test_cross_boundary_rename_retains_both_paths(
        self, tmp_path: Path
    ) -> None:
        root = _new_repository(tmp_path)
        (root / '.agents').mkdir(exist_ok=True)
        _git(root, 'mv', 'src/product.py', '.agents/product.py')

        records = changed_records(root)
        assert len(records) == 1
        assert records[0].old_path == 'src/product.py'
        assert records[0].new_path == '.agents/product.py'
        assert set(changed_paths(root)) == {
            'src/product.py',
            '.agents/product.py',
        }
        assert 'rename from src/product.py' in unified_diff(root)

    def test_copy_detection_retains_an_unchanged_source(
        self, tmp_path: Path
    ) -> None:
        root = _new_repository(tmp_path)
        shutil.copy2(root / 'src/product.py', root / 'src/copy.py')
        _git(root, 'add', '--', 'src/copy.py')

        records = changed_records(root)

        assert any(
            record.status.startswith('C')
            and record.old_path == 'src/product.py'
            and record.new_path == 'src/copy.py'
            for record in records
        )

    def test_snapshots_and_reads_use_the_selected_scope(
        self, tmp_path: Path
    ) -> None:
        root = _new_repository(tmp_path)
        head = _git(root, 'rev-parse', 'HEAD').stdout.strip()

        indexed = indexed_paths(root)
        revision = revision_paths(root, head)
        for external_root in EXTERNAL_HARNESS_ROOTS:
            assert all(not path.startswith(external_root) for path in indexed)
            assert all(not path.startswith(external_root) for path in revision)
        with repository_snapshot(root) as snapshot:
            assert (snapshot / 'src/product.py').is_file()
            for external_root in EXTERNAL_HARNESS_ROOTS:
                assert not (snapshot / external_root / 'fixture.txt').exists()
        with repository_snapshot(root, scope='repository') as snapshot:
            for external_root in EXTERNAL_HARNESS_ROOTS:
                assert (snapshot / external_root / 'fixture.txt').is_file()
        assert read_text('src/product.py', root) == 'value = 1\n'
        assert read_text('src/product.py', root, head) == 'value = 1\n'
        for external_root in EXTERNAL_HARNESS_ROOTS:
            external_path = f'{external_root}fixture.txt'
            with pytest.raises(UnsafeRepositoryPathError):
                read_text(external_path, root)
            with pytest.raises(UnsafeRepositoryPathError):
                read_text(external_path, root, head)

    def test_malformed_name_status_output_fails_closed(self) -> None:
        with pytest.raises(GitInspectionError):
            parse_name_status(b'M\0src/product.py')
        with pytest.raises(GitInspectionError):
            parse_name_status(b'R100\0src/old.py\0')

    def test_invalid_revision_and_non_repository_fail_closed(
        self, tmp_path: Path
    ) -> None:
        repository = tmp_path / 'repository'
        repository.mkdir()
        root = _new_repository(repository)

        with pytest.raises(GitInspectionError):
            verify_revision('missing-revision', root)
        outside_repository = tmp_path / 'outside'
        outside_repository.mkdir()
        with pytest.raises(GitInspectionError):
            repository_root(outside_repository)
