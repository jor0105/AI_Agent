"""Regression tests for staged debug and bypass detection."""

from __future__ import annotations

from pathlib import Path

import check_diff_sanity as gate
import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _join_fixture(*parts: str) -> str:
    """Build a prohibited fixture without adding that token to this diff."""
    return ''.join(parts)


def _as_added_diff(path: str) -> str:
    """Return a synthetic all-added diff for one repository source file."""
    content = (REPOSITORY_ROOT / path).read_text(encoding='utf-8')
    added_lines = '\n'.join(f'+{line}' for line in content.splitlines())
    return (
        f'diff --git a/{path} b/{path}\n'
        f'--- a/{path}\n'
        f'+++ b/{path}\n'
        f'@@ -0,0 +1,{len(content.splitlines())} @@\n'
        f'{added_lines}\n'
    )


def _added_line_diff(path: str, content: str) -> str:
    """Return a synthetic diff containing one added line."""
    return (
        f'diff --git a/{path} b/{path}\n'
        f'--- a/{path}\n'
        f'+++ b/{path}\n'
        '@@ -0,0 +1 @@\n'
        f'+{content}\n'
    )


@pytest.mark.unit
class TestDiffSanity:
    """Ruff suppressions and debugging residue must be visible failures."""

    def test_rejects_noqa_even_when_a_reason_is_present(self):
        diff = (
            """diff --git a/src/demo.py b/src/demo.py
--- a/src/demo.py
+++ b/src/demo.py
@@ -0,0 +1 @@
+"""
            + _join_fixture(
                'value = 1  # no', 'qa: E501 -- reason: make lint pass'
            )
            + '\n'
        )

        errors = gate.scan_diff(diff)

        assert any(
            'Ruff suppression is forbidden' in error for error in errors
        )

    def test_rejects_raw_print_in_library_source(self):
        diff = (
            """diff --git a/src/demo.py b/src/demo.py
--- a/src/demo.py
+++ b/src/demo.py
@@ -0,0 +1 @@
+"""
            + _join_fixture('pri', "nt('debug')")
            + '\n'
        )

        errors = gate.scan_diff(diff)

        assert any(
            _join_fixture('raw pri', 'nt() call') in error for error in errors
        )

    def test_rejects_coverage_suppression(self):
        diff = (
            """diff --git a/src/demo.py b/src/demo.py
--- a/src/demo.py
+++ b/src/demo.py
@@ -0,0 +1 @@
+"""
            + _join_fixture('def uncovered():  # pragma: no ', 'cover')
            + '\n'
        )

        errors = gate.scan_diff(diff)

        assert any('coverage suppression' in error for error in errors)

    def test_rejects_raw_print_in_project_scripts_without_explicit_allowlist(
        self,
    ):
        diff = _added_line_diff(
            'scripts/demo.py', _join_fixture('pri', "nt('debug')")
        )

        errors = gate.scan_diff(diff)

        assert any(
            _join_fixture('raw pri', 'nt() call') in error for error in errors
        )

    def test_allows_raw_print_only_in_the_explicitly_allowed_file(self):
        diff = _added_line_diff(
            'scripts/demo.py', _join_fixture('pri', "nt('PASS [DEMO]')")
        )

        assert gate.scan_diff(diff, ['scripts/demo.py']) == []
        assert gate.scan_diff(diff, ['scripts/other.py'])

    @pytest.mark.parametrize(
        'marker',
        (
            '# ' + 'reason: temporary compatibility',
            '-- ' + 'reason: temporary compatibility',
        ),
    )
    def test_rejects_generic_bypass_reason_markers(self, marker):
        line = 'value = 1  ' + _join_fixture('# type', ': ignore ') + marker

        errors = gate.scan_diff(_added_line_diff('src/demo.py', line))

        assert any('[BYPASS]' in error for error in errors)

    def test_accepts_only_explicit_bypass_reason_format(self):
        line = (
            'value = 1  '
            + _join_fixture('# type', ': ignore ')
            + 'allow-bypass: temporary compatibility'
        )

        assert gate.scan_diff(_added_line_diff('src/demo.py', line)) == []

    def test_rejects_empty_explicit_bypass_reason(self):
        line = (
            'value = 1  '
            + _join_fixture('# type', ': ignore ')
            + 'allow-bypass:'
        )

        errors = gate.scan_diff(_added_line_diff('src/demo.py', line))

        assert any('[BYPASS]' in error for error in errors)

    def test_skips_source_owned_by_the_central_harness(self):
        diff = (
            """diff --git a/.agents/harness/demo.py b/.agents/harness/demo.py
--- a/.agents/harness/demo.py
+++ b/.agents/harness/demo.py
@@ -0,0 +1 @@
+"""
            + _join_fixture('pri', "nt('central harness output')")
            + '\n'
        )

        assert gate.scan_diff(diff) == []

    def test_gate_sources_can_be_staged_without_self_violation(self):
        source_paths = (
            'scripts/quality_gates/check_diff_sanity.py',
            'tests/quality_gates/test_diff_sanity_gate.py',
        )

        for path in source_paths:
            allowed = (path,) if path.endswith('check_diff_sanity.py') else ()
            assert gate.scan_diff(_as_added_diff(path), allowed) == []
