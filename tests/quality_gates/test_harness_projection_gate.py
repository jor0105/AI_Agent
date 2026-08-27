"""Regression tests for the project-owned harness projection verifier."""

from __future__ import annotations

import json
from pathlib import Path

import check_harness_projection as gate
import pytest


def _write_snapshot(snapshot: Path) -> Path:
    """Build a minimal valid staged harness projection fixture."""
    harness = snapshot / '.agents' / 'harness'
    component = snapshot / '.agents' / 'skills' / 'demo'
    harness.mkdir(parents=True)
    component.mkdir(parents=True)
    (component / 'SKILL.md').write_text('# Demo\n', encoding='utf-8')
    (snapshot / '.agents' / 'harness.json').write_text(
        json.dumps({'version': '1.0.0', 'components': {'skills': ['demo']}}),
        encoding='utf-8',
    )
    (harness / 'components.json').write_text(
        json.dumps(
            {
                'components': {
                    'skills/demo': {
                        'source': 'skills/demo',
                        'requires': [],
                        'hasScripts': False,
                    }
                }
            }
        ),
        encoding='utf-8',
    )
    lock = {
        'centralVersion': '1.0.0',
        'components': [
            {
                'id': 'skills/demo',
                'hash': gate.component_hash(component),
                'hasScripts': False,
                'selectedBy': 'manifest',
            }
        ],
        'managedPaths': ['.agents/harness', '.agents/skills/demo'],
        'replacements': [],
    }
    (snapshot / '.agents' / 'harness.lock.json').write_text(
        json.dumps(lock), encoding='utf-8'
    )
    return component


@pytest.mark.unit
class TestHarnessProjection:
    """The lock must prove the exact projected component content."""

    def test_accepts_a_projection_that_matches_its_lock(self, tmp_path):
        _write_snapshot(tmp_path)

        assert gate.validate_harness_projection(tmp_path) == []

    def test_rejects_projection_content_that_does_not_match_the_lock(
        self, tmp_path
    ):
        component = _write_snapshot(tmp_path)
        (component / 'SKILL.md').write_text('# Modified\n', encoding='utf-8')

        errors = gate.validate_harness_projection(tmp_path)

        assert any('projection hash differs' in error for error in errors)

    def test_rejects_lock_content_outside_the_manifest_closure(self, tmp_path):
        _write_snapshot(tmp_path)
        manifest_path = tmp_path / '.agents' / 'harness.json'
        manifest_path.write_text(
            json.dumps({'version': '1.0.0', 'components': {'skills': []}}),
            encoding='utf-8',
        )

        errors = gate.validate_harness_projection(tmp_path)

        assert any('dependency closure' in error for error in errors)
