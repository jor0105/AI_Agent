"""Tests for the complete local quality-gate policy."""

from __future__ import annotations

import re
import shutil
from contextlib import nullcontext
from pathlib import Path

import pytest
import quality_gate_policy as gate
from git_changes import StagedChange
from hook_config import _parse_hook_blocks
from hook_policy import _MUTATING_HOOKS, _validate_pre_commit_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    """Read a repository policy fixture from the current working tree."""
    return (REPOSITORY_ROOT / path).read_text(encoding='utf-8')


def _validate(pre_commit: str | None = None) -> list[str]:
    """Validate the current hook policy with one optional mutation."""
    return _validate_pre_commit_config(
        pre_commit
        if pre_commit is not None
        else _read('.pre-commit-config.yaml')
    )


def _policy_snapshot(tmp_path: Path) -> Path:
    """Copy every policy-owned tracked input into an isolated snapshot."""
    snapshot = tmp_path / 'snapshot'
    for relative in gate._REQUIRED_PATHS:
        source = REPOSITORY_ROOT / relative
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    optional_ignore = REPOSITORY_ROOT / '.gitleaksignore'
    if optional_ignore.is_file():
        shutil.copy2(optional_ignore, snapshot / '.gitleaksignore')
    return snapshot


def _replace(snapshot: Path, relative: str, old: str, new: str) -> None:
    """Apply one asserted textual policy mutation."""
    path = snapshot / relative
    content = path.read_text(encoding='utf-8')
    assert old in content
    path.write_text(content.replace(old, new, 1), encoding='utf-8')


@pytest.mark.unit
class TestQualityGatePolicy:
    """The policy protects lifecycle, safety, and ownership invariants."""

    def test_current_policy_is_valid(self) -> None:
        assert _validate() == []
        assert gate.validate_quality_policy(REPOSITORY_ROOT) == []

    def test_mutating_hooks_exclude_every_external_root(self) -> None:
        blocks = _parse_hook_blocks(_read('.pre-commit-config.yaml'))
        external_files = (
            '.agents/fixture.txt',
            '.claude/fixture.txt',
            '.codex/fixture.txt',
            '.opencode/fixture.txt',
            '.github/prompts/fixture.txt',
        )

        for hook_id in _MUTATING_HOOKS:
            exclusion = re.compile(blocks[hook_id].value('exclude'))
            assert all(exclusion.search(path) for path in external_files)

    def test_runner_accepts_a_complete_valid_staged_policy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(gate, 'repository_root', lambda: REPOSITORY_ROOT)
        monkeypatch.setattr(
            gate,
            'changed_records',
            lambda root: [StagedChange('M', None, '.pre-commit-config.yaml')],
        )
        monkeypatch.setattr(
            gate,
            'repository_snapshot',
            lambda root, scope: nullcontext(REPOSITORY_ROOT),
        )

        assert gate.main([]) == 0
        assert 'PASS [QUALITY_GATE_POLICY]' in capsys.readouterr().out

    def test_runner_rejects_a_missing_staged_configuration(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        snapshot = REPOSITORY_ROOT / 'missing-quality-snapshot'
        monkeypatch.setattr(gate, 'repository_root', lambda: REPOSITORY_ROOT)
        monkeypatch.setattr(
            gate,
            'changed_records',
            lambda root: [StagedChange('M', None, '.pre-commit-config.yaml')],
        )
        monkeypatch.setattr(
            gate,
            'repository_snapshot',
            lambda root, scope: nullcontext(snapshot),
        )

        assert gate.main([]) == 1
        assert 'must exist and be tracked' in capsys.readouterr().err

    def test_rejects_an_unpinned_remote_hook(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            '3e8a8703264a2f4a69428a0aa4dcb512790b2c8c', 'v6.0.0', 1
        )
        assert any('40-character SHA' in error for error in _validate(config))

    def test_rejects_uv_runs_that_can_sync_the_environment(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            'uv run --locked --no-sync', 'uv run --locked', 1
        )
        assert any(
            'locked no-sync' in error or '--locked --no-sync' in error
            for error in _validate(config)
        )

    def test_rejects_a_reintroduced_pydocstyle_hook(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            '      - id: import-cycles\n',
            '      - id: pydocstyle\n'
            '        entry: pydocstyle src\n'
            '      - id: import-cycles\n',
            1,
        )
        assert any('pydocstyle' in error for error in _validate(config))

    def test_requires_visible_ruff_autofix_failure(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            'args: [--fix, --exit-non-zero-on-fix]', 'args: [--fix]', 1
        )
        assert any(
            'safe auto-fix failure mode' in error
            for error in _validate(config)
        )

    def test_requires_a_bounded_pip_audit_timeout(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            'pip-audit --timeout 60', 'pip-audit', 1
        )
        assert any(
            'pip-audit must use --timeout 60' in error
            for error in _validate(config)
        )

    def test_rejects_the_mutating_uv_lock_hook(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            '- id: lockfile-sync', '- id: uv-lock', 1
        )
        assert any('uv-lock mutates' in error for error in _validate(config))

    @pytest.mark.parametrize(
        'mirror',
        (
            r'\.agents/',
            r'\.claude/',
            r'\.codex/',
            r'\.opencode/',
            r'\.github/prompts/',
        ),
    )
    def test_rejects_a_missing_generated_projection_exclusion(
        self, mirror: str
    ) -> None:
        suffix = '\n' if mirror.endswith('prompts/') else '|\n'
        target = f'            {mirror}{suffix}'
        config = _read('.pre-commit-config.yaml')
        assert target in config

        config = config.replace(target, '', 1)
        assert any(
            'generated mirrors must remain excluded' in error
            for error in _validate(config)
        )

    def test_rejects_a_missing_required_gate(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            '- id: test-integrity', '- id: omitted-test-integrity', 1
        )
        assert any('test-integrity' in error for error in _validate(config))

    def test_rejects_test_integrity_without_always_run(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            '        always_run: true\n', '', 1
        )
        assert any(
            'must remain always_run' in error for error in _validate(config)
        )

    def test_rejects_manual_harness_sync_outside_exact_contract(self) -> None:
        token = 'harness-' + 'sync'
        config = _read('.pre-commit-config.yaml').replace(
            '      - id: check-harness-sync',
            f'      - id: other-hook\n        entry: {token} --check\n'
            '      - id: check-harness-sync',
            1,
        )
        assert any('harness-sync' in error for error in _validate(config))

    def test_rejects_coverage_duplication(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            '          --cov\n', '          --cov --cov=src\n', 1
        )
        assert any('coverage' in error for error in _validate(config))

    @pytest.mark.parametrize(
        ('old', 'new', 'message'),
        (
            (
                'minimum_pre_commit_version: "4.6.2"',
                'minimum_pre_commit_version: "4.6.1"',
                'minimum_pre_commit_version',
            ),
            (
                'minimum_pre_commit_version: "4.6.2"',
                'minimum_pre_commit_version: "4.6.2"\n'
                'default_language_version: {python: python3.12}',
                'global Python hook-environment pin',
            ),
            (
                'args: [--redact, --config=.gitleaks.toml]',
                'args: [--config=.gitleaks.toml]',
                'gitleaks must use exactly',
            ),
            (
                'files: ^AGENTS\\.md$',
                'files: ^docs/.*\\.md$',
                'root AGENTS.md',
            ),
            (
                'args: [src, tests, scripts]',
                'args: [src, tests]',
                'exactly src, tests, and scripts',
            ),
            (
                'files: ^(?:src|tests|scripts)/.*\\.(?:py|pyi|pyw|sh|bash)$',
                'files: ^src/.*\\.py$',
                'codespell must cover',
            ),
            (
                '--allow-print-file=scripts/check-import-cycles.py',
                '--allow-print-file=scripts',
                'exact repository print allowlist',
            ),
            (
                'scripts/quality_gates/check_lockfile_sync.py',
                'scripts/quality_gates/check_test_integrity.py',
                'lockfile-sync: entry must remain',
            ),
            (
                'entry: uv run --locked --no-sync lint-imports',
                'entry: pip install unexpected-tool',
                'forbidden non-reproducible',
            ),
        ),
    )
    def test_rejects_each_hook_contract_mutation(
        self, old: str, new: str, message: str
    ) -> None:
        config = _read('.pre-commit-config.yaml')
        assert old in config

        assert any(
            message in error
            for error in _validate(config.replace(old, new, 1))
        )

    def test_rejects_gitleaks_selection_weakening(self) -> None:
        original = (
            '        args: [--redact, --config=.gitleaks.toml]\n'
            '        pass_filenames: false\n'
            '        always_run: true'
        )
        weakened = original.replace(
            'pass_filenames: false', 'pass_filenames: true'
        )
        config = _read('.pre-commit-config.yaml')
        assert original in config

        assert any(
            'complete tracked repository' in error
            for error in _validate(config.replace(original, weakened, 1))
        )

    def test_rejects_pre_push_stage_drift(self) -> None:
        config = _read('.pre-commit-config.yaml').replace(
            '        stages: [pre-push]', '        stages: [pre-commit]', 1
        )

        assert any(
            'must remain in the [pre-push]' in error
            for error in _validate(config)
        )

    def test_rejects_hook_bypass_entry(self) -> None:
        bypass = '--no' + '-verify'
        config = _read('.pre-commit-config.yaml').replace(
            'entry: uv run --locked --no-sync lint-imports',
            f'entry: git commit {bypass}',
            1,
        )

        assert any('forbidden' in error for error in _validate(config))

    def test_missing_owned_module_fails_snapshot_policy(
        self, tmp_path: Path
    ) -> None:
        snapshot = _policy_snapshot(tmp_path)
        (snapshot / 'scripts/quality_gates/process_runner.py').unlink()

        errors = gate.validate_quality_policy(snapshot)

        assert any(
            'process_runner.py must exist and be tracked' in error
            for error in errors
        )

    def test_rejects_weakened_gitleaks_policy_and_broad_ignore(
        self, tmp_path: Path
    ) -> None:
        snapshot = _policy_snapshot(tmp_path)
        (snapshot / '.gitleaks.toml').write_text(
            _read('.gitleaks.toml') + '\n[[allowlists]]\npaths = ["src/"]\n',
            encoding='utf-8',
        )
        (snapshot / '.gitleaksignore').write_text(
            '.agents/\n', encoding='utf-8'
        )

        errors = gate.validate_quality_policy(snapshot)

        assert any('minimal default-rule policy' in error for error in errors)
        assert any('broad path ignores' in error for error in errors)

    @pytest.mark.parametrize(
        ('old', 'new', 'message'),
        (
            ('pre-commit>=4.6.2', 'pre-commit>=4.6.1', 'lower bound'),
            (
                'mypy_path = ["src", "scripts/quality_gates"]',
                'mypy_path = ["src"]',
                'search src and scripts/quality_gates',
            ),
            (
                'explicit_package_bases = true',
                'explicit_package_bases = false',
                'explicit_package_bases',
            ),
            (
                'warn_return_any = true',
                'ignore_missing_imports = true\nwarn_return_any = true',
                'broad Mypy import suppression',
            ),
            (
                'release = [',
                'release-disabled = [',
                'release dependency group',
            ),
            ('    "D",', '    "S",', 'Ruff must own the D'),
            ('    "T201",', '    "T20",', 'Ruff must own the T201'),
            ('    "C901",', '    "C90",', 'Ruff must own the C901'),
            ('    "D",', '    "D", "S",', 'Ruff security S rules'),
        ),
    )
    def test_rejects_pyproject_policy_mutations(
        self, tmp_path: Path, old: str, new: str, message: str
    ) -> None:
        snapshot = _policy_snapshot(tmp_path)
        _replace(snapshot, 'pyproject.toml', old, new)

        assert any(
            message in error
            for error in gate.validate_quality_policy(snapshot)
        )

    def test_rejects_pytest_coverage_owner_drift(self, tmp_path: Path) -> None:
        snapshot = _policy_snapshot(tmp_path)
        _replace(snapshot, 'pytest.ini', 'fail_under = 85', 'fail_under = 80')

        assert any(
            'fail_under = 85' in error
            for error in gate.validate_quality_policy(snapshot)
        )

    @pytest.mark.parametrize(
        ('relative', 'old', 'new', 'message'),
        (
            (
                '.github/workflows/pipeline.yml',
                'GITLEAKS_ENABLE_COMMENTS: "false"',
                'GITLEAKS_ENABLE_COMMENTS: "true"',
                'GITLEAKS_ENABLE_COMMENTS',
            ),
            (
                '.github/workflows/pipeline.yml',
                'uv run --locked --no-sync pip-audit --timeout 60',
                'uv run pip-audit',
                'pip-audit --timeout 60',
            ),
            (
                '.github/workflows/docs.yml',
                'uv run --locked --no-sync mkdocs build --strict',
                'uv run mkdocs build',
                'docs.yml is missing required command',
            ),
            (
                '.github/workflows/publish.yml',
                'uv sync --locked --no-dev --group release',
                'uv sync --locked --with twine',
                'locked release dependency group',
            ),
        ),
    )
    def test_rejects_workflow_parity_mutations(
        self, tmp_path: Path, relative: str, old: str, new: str, message: str
    ) -> None:
        snapshot = _policy_snapshot(tmp_path)
        _replace(snapshot, relative, old, new)

        assert any(
            message in error
            for error in gate.validate_quality_policy(snapshot)
        )

    def test_future_product_shell_requires_a_syntax_gate(
        self, tmp_path: Path
    ) -> None:
        snapshot = _policy_snapshot(tmp_path)
        shell_file = snapshot / 'scripts' / 'future-check.sh'
        shell_file.write_text(
            '#!/usr/bin/env bash\nexit 0\n', encoding='utf-8'
        )

        assert any(
            'shell-syntax hook' in error
            for error in gate.validate_quality_policy(snapshot)
        )
