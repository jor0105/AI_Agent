"""Slow regressions for the tracked-file Gitleaks boundary."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

GITLEAKS_REPOSITORY = 'https://github.com/gitleaks/gitleaks'
GITLEAKS_REVISION = '2ca41cc1372d1e939a6a879f18cdc19fc1cac1ce'


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ['git', *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


def _prepare_repository(root: Path, target: str, content: str) -> None:
    _git(root, 'init')
    _git(root, 'config', 'user.email', 'quality@example.invalid')
    _git(root, 'config', 'user.name', 'Quality Gate')
    (root / '.gitleaks.toml').write_text(
        'title = "Create Agents AI gitleaks policy"\n\n'
        '[extend]\n'
        'useDefault = true\n',
        encoding='utf-8',
    )
    (root / '.pre-commit-config.yaml').write_text(
        f'repos:\n- repo: {GITLEAKS_REPOSITORY}\n'
        f'  rev: {GITLEAKS_REVISION}\n'
        '  hooks:\n  - id: gitleaks\n'
        '    args: [--redact, --config=.gitleaks.toml]\n'
        '    pass_filenames: false\n'
        '    always_run: true\n',
        encoding='utf-8',
    )
    target_path = root / target / 'fixture.txt'
    target_path.parent.mkdir(parents=True)
    target_path.write_text(content, encoding='utf-8')
    _git(
        root, 'add', '--', '.gitleaks.toml', '.pre-commit-config.yaml', target
    )


def _run_gitleaks(root: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ | {
        'PRE_COMMIT_CONFIG': str(root / '.pre-commit-config.yaml')
    }
    return subprocess.run(
        [sys.executable, '-m', 'pre_commit', 'run', 'gitleaks', '--all-files'],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


@pytest.mark.slow
@pytest.mark.parametrize('target', ('.agents', 'src'))
def test_pinned_gitleaks_scans_tracked_harness_and_product_files(
    tmp_path: Path, target: str
) -> None:
    secret = 'AK' + 'IA' + '2QWERTYUIOPASDFG'
    _prepare_repository(tmp_path, target, f'credential = {secret}\n')
    result = _run_gitleaks(tmp_path)
    output = result.stdout + result.stderr

    if 'An error has occurred' in output and secret not in output:
        pytest.skip('pinned Gitleaks hook environment is unavailable')

    assert result.returncode != 0
    assert secret not in output


@pytest.mark.slow
def test_pinned_gitleaks_accepts_a_tracked_safe_control(
    tmp_path: Path,
) -> None:
    _prepare_repository(
        tmp_path,
        'src',
        'message = this fixture intentionally contains no credential\n',
    )

    result = _run_gitleaks(tmp_path)
    output = result.stdout + result.stderr

    if 'An error has occurred' in output:
        pytest.skip('pinned Gitleaks hook environment is unavailable')

    assert result.returncode == 0, output
    assert not (tmp_path / '.gitleaksignore').exists()
    assert (tmp_path / '.gitleaks.toml').read_text(encoding='utf-8') == (
        'title = "Create Agents AI gitleaks policy"\n\n'
        '[extend]\n'
        'useDefault = true\n'
    )
