"""Tests for the focused local quality-gate policy."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import quality_gate_policy as gate

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    """Read a repository policy fixture from the current working tree."""
    return (REPOSITORY_ROOT / path).read_text(encoding='utf-8')


def _validate(pre_commit: str | None = None) -> list[str]:
    """Validate the current hook policy with one optional mutation."""
    return gate.validate_quality_gate_config(
        pre_commit or _read('.pre-commit-config.yaml')
    )


@pytest.mark.unit
class TestQualityGatePolicy:
    """The policy protects only the lifecycle and safety invariants."""

    def test_current_policy_is_valid(self):
        assert _validate() == []

    def test_runner_accepts_a_complete_valid_staged_policy(
        self, monkeypatch, capsys
    ):
        monkeypatch.setattr(gate, 'repository_root', lambda: REPOSITORY_ROOT)
        monkeypatch.setattr(
            gate,
            'staged_changes',
            lambda root: [SimpleNamespace(new_path='.pre-commit-config.yaml')],
        )
        monkeypatch.setattr(
            gate,
            'read_index_text',
            lambda path, root: _read('.pre-commit-config.yaml'),
        )

        assert gate.main() == 0
        assert 'PASS [QUALITY_GATE_POLICY]' in capsys.readouterr().out

    def test_runner_rejects_a_missing_staged_configuration(
        self, monkeypatch, capsys
    ):
        monkeypatch.setattr(gate, 'repository_root', lambda: REPOSITORY_ROOT)
        monkeypatch.setattr(
            gate,
            'staged_changes',
            lambda root: [SimpleNamespace(new_path='.pre-commit-config.yaml')],
        )
        monkeypatch.setattr(gate, 'read_index_text', lambda path, root: None)

        assert gate.main() == 1
        assert '.pre-commit-config.yaml is absent from the index' in (
            capsys.readouterr().err
        )

    def test_rejects_an_unpinned_remote_hook(self):
        config = _read('.pre-commit-config.yaml').replace(
            '3e8a8703264a2f4a69428a0aa4dcb512790b2c8c', 'v6.0.0', 1
        )

        assert any('40-character SHA' in error for error in _validate(config))

    def test_rejects_uv_runs_that_can_sync_the_environment(self):
        config = _read('.pre-commit-config.yaml').replace(
            'uv run --locked --no-sync', 'uv run --locked', 1
        )

        assert any(
            '--locked --no-sync' in error for error in _validate(config)
        )

    def test_rejects_the_mutating_uv_lock_hook(self):
        config = _read('.pre-commit-config.yaml').replace(
            '- id: lockfile-sync', '- id: uv-lock', 1
        )

        assert any('uv-lock mutates' in error for error in _validate(config))

    def test_rejects_a_missing_generated_projection_exclusion(self):
        config = _read('.pre-commit-config.yaml').replace(
            '            \\.agents/|\n', '', 1
        )

        assert any(
            'generated mirrors must remain excluded' in error
            for error in _validate(config)
        )

    def test_rejects_a_missing_required_gate(self):
        config = _read('.pre-commit-config.yaml').replace(
            '- id: test-integrity', '- id: omitted-test-integrity', 1
        )

        assert any('test-integrity' in error for error in _validate(config))

    def test_rejects_a_pre_push_gate_in_the_wrong_stage(self):
        config = _read('.pre-commit-config.yaml').replace(
            'stages: [pre-push]', 'stages: [pre-commit]', 1
        )

        assert any(
            'mypy-pre-push: must remain' in error
            for error in _validate(config)
        )
