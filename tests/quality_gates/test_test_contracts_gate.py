"""Tests for the AST test-contract quality gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'quality_gates')
)

import check_test_contracts as gate


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ['git', *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.mark.unit
class TestTestContractsGate:
    def test_clean_valid_test_and_dunder_methods_pass(self):
        source = """
from functools import wraps
import pytest

class Example:
    def __init__(self):
        self.value = 1

    def __iter__(self):
        return iter((self.value,))

def original():
    return 'value'

@wraps(original)
def decorated():
    return original()

def test_valid_addition():
    actual = 1 + 1
    assert actual == 2

@pytest.mark.asyncio
async def test_valid_async():
    with pytest.raises(ValueError):
        raise ValueError('boom')
"""

        assert gate.audit_source(source, 'tests/test_example.py') == []

    def test_detects_direct_hasattr_call(self):
        source = """
def test_hasattr_bad():
    obj = object()
    assert hasattr(obj, 'foo')
"""

        violations = gate.audit_source(source, 'tests/test_example.py')

        assert [violation.category for violation in violations] == [
            'HASATTR_PROHIBITED'
        ]

    @pytest.mark.parametrize(
        'source',
        [
            """
import builtins
def test_qualified_hasattr():
    assert builtins.hasattr(object(), 'foo')
""",
            """
from builtins import hasattr as has_attribute
def test_aliased_hasattr():
    assert has_attribute(object(), 'foo')
""",
        ],
    )
    def test_detects_qualified_and_aliased_hasattr(self, source):
        violations = gate.audit_source(source, 'tests/test_example.py')

        assert any(
            violation.category == 'HASATTR_PROHIBITED'
            for violation in violations
        )

    def test_detects_name_mangled_attribute_with_underscored_class(self):
        source = """
def test_mangled():
    client = MyClient()
    value = client._Foo_Bar__secret
    assert value == 1
"""

        violations = gate.audit_source(source, 'tests/test_example.py')

        assert [violation.category for violation in violations] == [
            'NAME_MANGLING_PROHIBITED'
        ]

    @pytest.mark.parametrize(
        'source',
        [
            """
TARGET = '_Foo_Bar__secret'
def test_dynamic_getattr():
    assert getattr(object(), TARGET)
""",
            """
def test_dynamic_setattr_and_delattr():
    setattr(object(), '_Foo_Bar__secret', 1)
    delattr(object(), '_Foo_Bar__secret')
    assert value == 1
""",
        ],
    )
    def test_detects_dynamic_name_mangled_access(self, source):
        violations = gate.audit_source(source, 'tests/test_example.py')

        assert (
            sum(
                violation.category == 'DYNAMIC_NAME_MANGLING_PROHIBITED'
                for violation in violations
            )
            >= 1
        )

    @pytest.mark.parametrize(
        'source',
        [
            """
from unittest.mock import patch
def test_private_patch_target():
    with patch('module.Foo._Foo_Bar__secret'):
        assert value == 1
""",
            """
from unittest.mock import patch as mock_patch
def test_private_patch_object_target():
    with mock_patch.object(Foo, '_Foo_Bar__secret'):
        assert value == 1
""",
        ],
    )
    def test_detects_private_patch_target_strings(self, source):
        violations = gate.audit_source(source, 'tests/test_example.py')

        assert any(
            violation.category == 'DYNAMIC_NAME_MANGLING_PROHIBITED'
            for violation in violations
        )

    def test_detects_factory_clear_cache_aliases(self):
        source = """
from createagents.infra import ChatAdapterFactory as Factory
factory = Factory
def test_factory_cache():
    factory.clear_cache()
    assert result == 1
"""

        violations = gate.audit_source(source, 'tests/test_example.py')

        assert any(
            violation.category == 'RETIRED_FACTORY_CACHE'
            for violation in violations
        )

    def test_detects_transitive_factory_clear_cache_aliases(self):
        source = """
from createagents.infra import ChatAdapterFactory as Factory
factory = later_factory
later_factory = Factory
def test_factory_cache():
    factory.clear_cache()
    assert result == 1
"""

        violations = gate.audit_source(source, 'tests/test_example.py')

        assert any(
            violation.category == 'RETIRED_FACTORY_CACHE'
            for violation in violations
        )

    def test_allows_non_factory_clear_cache_calls(self):
        source = """
def test_valid_cache_reset():
    EnvironmentConfig.clear_cache()
    SensitiveDataFilter.clear_cache()
    assert result == 1
"""

        assert gate.audit_source(source, 'tests/test_example.py') == []

    def test_detects_constant_assertion_outcomes(self):
        source = """
def test_truthy_constant():
    assert True

def test_falsy_constant():
    assert 1 == 2
"""

        violations = gate.audit_source(source, 'tests/test_example.py')

        assert (
            sum(
                violation.category == 'TAUTOLOGICAL_ASSERTION'
                for violation in violations
            )
            == 2
        )

    @pytest.mark.parametrize(
        ('expression', 'outcome'),
        [
            ('1 in (1,)', 'truthy'),
            ('2 in (1,)', 'falsy'),
            ('1 not in (1,)', 'falsy'),
            ('2 not in (1,)', 'truthy'),
        ],
    )
    def test_detects_constant_membership_assertions(self, expression, outcome):
        source = f"""
def test_constant_membership():
    assert {expression}
"""

        violations = gate.audit_source(source, 'tests/test_example.py')

        assert [violation.category for violation in violations] == [
            'TAUTOLOGICAL_ASSERTION'
        ]
        assert f'constant {outcome} outcome' in violations[0].message

    def test_detects_tautological_boolean_branches(self):
        source = """
def test_tautology_or(value):
    assert value == 5 or True

def test_tautology_and(value):
    assert value == 5 and False
"""

        violations = gate.audit_source(source, 'tests/test_example.py')

        assert (
            sum(
                violation.category == 'TAUTOLOGICAL_ASSERTION'
                for violation in violations
            )
            == 2
        )

    def test_detects_pass_and_empty_test_body(self):
        source = """
def test_pass_statement():
    pass
"""

        violations = gate.audit_source(source, 'tests/test_example.py')
        categories = [violation.category for violation in violations]

        assert 'PASS_PROHIBITED' in categories
        assert 'EMPTY_TEST_BODY' in categories

    def test_detects_empty_test_without_evidence(self):
        source = """
def test_no_assertions():
    value = 1 + 2
"""

        violations = gate.audit_source(source, 'tests/test_example.py')

        assert [violation.category for violation in violations] == [
            'EMPTY_TEST_BODY'
        ]

    @pytest.mark.parametrize(
        'source',
        [
            """
import pytest
def test_expected_exception():
    with pytest.raises(ValueError):
        raise ValueError('bad')
""",
            """
import pytest
def test_warning_context():
    with pytest.warns(UserWarning):
        raise UserWarning('bad')
""",
            """
import pytest
def test_explicit_skip():
    pytest.skip('not applicable in this fixture')
""",
        ],
    )
    def test_allows_explicit_test_outcomes(self, source):
        assert gate.audit_source(source, 'tests/test_example.py') == []

    @pytest.mark.parametrize(
        'source',
        [
            """
def test_silent_pass():
    try:
        raise ValueError('bad')
    except ValueError:
        pass
    assert result == 1
""",
            """
def test_silent_return():
    try:
        raise ValueError('bad')
    except ValueError:
        return None
    assert result == 1
""",
        ],
    )
    def test_detects_silent_exception_handlers(self, source):
        violations = gate.audit_source(source, 'tests/test_example.py')

        assert any(
            violation.category == 'SILENT_EXCEPTION_SWALLOW'
            for violation in violations
        )

    def test_allows_intentional_fixture_strings_and_wraps_metadata(self):
        source = """
from functools import wraps

FIXTURE_TEXT = 'Markdown uses __bold__ and a source example: _Foo_Bar__secret'

def original():
    return FIXTURE_TEXT

@wraps(original)
def decorated():
    return original()

def test_fixture_text():
    assert decorated.__name__ == 'original'
"""

        assert gate.audit_source(source, 'tests/test_example.py') == []

    def test_syntax_errors_fail_closed(self):
        violations = gate.audit_source(
            'def test_broken(:\n    assert value == 1\n',
            'tests/test_example.py',
        )

        assert violations[0].category == 'SYNTAX_ERROR'

    def test_runner_audits_complete_index_snapshot(self, monkeypatch, capsys):
        contents = {
            'tests/unchanged.py': """
def test_unchanged_bad():
    assert hasattr(object(), 'value')
""",
            'tests/changed.py': """
def test_changed_good():
    value = 1
    assert value == 1
""",
        }
        monkeypatch.setattr(gate, 'repository_root', lambda: Path.cwd())
        monkeypatch.setattr(
            gate,
            'indexed_paths',
            lambda root: [
                'tests/unchanged.py',
                'tests/changed.py',
                'src/not_a_test.py',
            ],
        )
        monkeypatch.setattr(
            gate,
            'read_text',
            lambda path, root: contents.get(path),
        )

        assert gate.main([]) == 1
        assert 'tests/unchanged.py' in capsys.readouterr().err

    def test_complete_revision_audit_reads_the_exact_commit(
        self, tmp_path: Path
    ) -> None:
        _git(tmp_path, 'init')
        _git(tmp_path, 'config', 'user.email', 'quality@example.invalid')
        _git(tmp_path, 'config', 'user.name', 'Quality Gate')
        test_file = tmp_path / 'tests' / 'test_contract.py'
        test_file.parent.mkdir()
        test_file.write_text(
            'def test_contract(value):\n    assert value is not None\n',
            encoding='utf-8',
        )
        _git(tmp_path, 'add', '--', 'tests/test_contract.py')
        _git(tmp_path, 'commit', '-m', 'valid contract')
        valid_revision = _git(tmp_path, 'rev-parse', 'HEAD')

        test_file.write_text(
            "def test_contract(value):\n    assert hasattr(value, 'field')\n",
            encoding='utf-8',
        )
        _git(tmp_path, 'add', '--', 'tests/test_contract.py')
        _git(tmp_path, 'commit', '-m', 'invalid contract')
        invalid_revision = _git(tmp_path, 'rev-parse', 'HEAD')

        assert gate.audit_test_files(tmp_path, revision=valid_revision) == []
        violations = gate.audit_test_files(tmp_path, revision=invalid_revision)
        assert [violation.category for violation in violations] == [
            'HASATTR_PROHIBITED'
        ]

    def test_complete_discovery_excludes_external_test_projections(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            gate,
            'indexed_paths',
            lambda root: [
                '.agents/tests/test_external.py',
                'tests/test_product.py',
            ],
        )
        monkeypatch.setattr(
            gate,
            'read_text',
            lambda path, root: (
                'def test_bad():\n    assert hasattr(object(), "x")\n'
                if path.startswith('.agents/')
                else 'def test_good():\n    assert 1 == 1\n'
            ),
        )

        violations = gate.audit_test_files(Path.cwd())

        assert [violation.file_path for violation in violations] == [
            'tests/test_product.py'
        ]
