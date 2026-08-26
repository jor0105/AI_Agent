"""Regression tests for the staged test-integrity gate."""

from __future__ import annotations

from pathlib import Path

import check_test_integrity as gate
import pytest


def _join_fixture(*parts: str) -> str:
    """Build a prohibited fixture without adding that token to this diff."""
    return ''.join(parts)


def _assertion_reduction_diff() -> str:
    """Return a test diff with a net assertion reduction."""
    return """diff --git a/tests/test_guard.py b/tests/test_guard.py
--- a/tests/test_guard.py
+++ b/tests/test_guard.py
@@ -1,4 +1,3 @@
 def test_guard():
-    assert first_condition()
-    assert second_condition()
+    assert first_condition()
"""


@pytest.mark.unit
class TestStagedTestIntegrity:
    """The gate must never trust an unstaged reason file."""

    def test_unstaged_reason_cannot_authorize_assertion_reduction(
        self, tmp_path
    ):
        test_file = tmp_path / 'tests' / 'test_guard.py'
        test_file.parent.mkdir()
        test_file.write_text(
            '# allow-assertion-reduction: this is only in the working tree\n',
            encoding='utf-8',
        )
        errors = gate.scan_test_integrity(
            _assertion_reduction_diff(), tmp_path
        )

        assert any('[TEST_INTEGRITY]' in error for error in errors)

    def test_staged_reason_can_be_reviewed_with_the_reduction(self, tmp_path):
        diff = """diff --git a/tests/test_guard.py b/tests/test_guard.py
--- a/tests/test_guard.py
+++ b/tests/test_guard.py
@@ -1,4 +1,4 @@
 def test_guard():
-    assert first_condition()
-    assert second_condition()
+    # allow-assertion-reduction: redundant behavior is proven by the integration contract
+    assert first_condition()
"""

        assert gate.scan_test_integrity(diff, tmp_path) == []

    def test_focused_test_is_never_allowed(self, tmp_path):
        diff = (
            """diff --git a/tests/test_guard.py b/tests/test_guard.py
--- a/tests/test_guard.py
+++ b/tests/test_guard.py
@@ -0,0 +1 @@
+"""
            + _join_fixture(
                'test.', "only('guard', lambda: None)  # allow-skip: no effect"
            )
            + '\n'
        )

        errors = gate.scan_test_integrity(diff, tmp_path)

        assert any('[TEST_FOCUS]' in error for error in errors)

    def test_short_skip_reason_is_not_an_exception(self, tmp_path):
        diff = (
            """diff --git a/tests/test_guard.py b/tests/test_guard.py
--- a/tests/test_guard.py
+++ b/tests/test_guard.py
@@ -0,0 +1 @@
+"""
            + _join_fixture('@pytest.mark.', 'skip  # allow-skip: later')
            + '\n'
        )

        errors = gate.scan_test_integrity(diff, tmp_path)

        assert any('[TEST_SKIP]' in error for error in errors)

    def test_deletion_policy_is_read_from_the_index(
        self, tmp_path, monkeypatch
    ):
        policy = (
            '{"allowed_deletions": {"tests/test_guard.py": '
            '"Superseded by the maintained integration coverage."}}'
        )

        def staged_content(path: str, root: Path) -> str | None:
            return policy if path == '.test-deletions.json' else None

        monkeypatch.setattr(gate, 'read_index_text', staged_content)

        assert gate.is_test_deletion_approved('tests/test_guard.py', tmp_path)
