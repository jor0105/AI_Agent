"""Regression tests for staged debug and bypass detection."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from check_diff_sanity import main as diff_sanity_main
from diff_sanity_policy import scan_diff, validate_print_allowlist
from git_changes import unified_diff

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _join_fixture(*parts: str) -> str:
    """Build a prohibited fixture without adding that token to this source."""
    return ''.join(parts)


def _added_line_diff(path: str, content: str) -> str:
    """Return a synthetic diff containing one added line."""
    return (
        f'diff --git a/{path} b/{path}\n'
        f'--- a/{path}\n'
        f'+++ b/{path}\n'
        '@@ -0,0 +1 @@\n'
        f'+{content}\n'
    )


def _errors(path: str, content: str) -> list[str]:
    return scan_diff(_added_line_diff(path, content))


def _git(root: Path, *args: str) -> str:
    """Run Git in an isolated regression repository."""
    return subprocess.run(
        ['git', *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.mark.unit
class TestDiffSanity:
    """Unsafe additions remain failures without comment-based exceptions."""

    @pytest.mark.parametrize(
        ('path', 'content', 'category'),
        (
            ('src/demo.py', _join_fixture('break', 'point()'), '[DEBUG]'),
            ('src/demo.py', _join_fixture('pdb.', 'set_trace()'), '[DEBUG]'),
            ('src/demo.py', _join_fixture('debug', 'ger;'), '[DEBUG]'),
            ('src/demo.js', _join_fixture('console.', 'log(1)'), '[DEBUG]'),
            ('src/demo.js', _join_fixture('console.', 'debug(1)'), '[DEBUG]'),
            ('src/demo.js', _join_fixture('console.', 'trace(1)'), '[DEBUG]'),
            (
                'src/demo.js',
                _join_fixture('console.', 'dir(value)'),
                '[DEBUG]',
            ),
            (
                'src/demo.py',
                _join_fixture('raise ', 'Not', 'Implemented', 'Error("TODO")'),
                '[STUB]',
            ),
            ('src/demo.py', _join_fixture('pass # ', 'TO', 'DO'), '[STUB]'),
            (
                'src/demo.js',
                _join_fixture('throw new Error("', 'TO', 'DO")'),
                '[STUB]',
            ),
        ),
    )
    def test_unconditional_debug_and_stub_patterns(
        self, path: str, content: str, category: str
    ) -> None:
        errors = _errors(
            path,
            content + ' # ' + _join_fixture('allow-', 'debug') + ': reason',
        )
        assert any(category in error for error in errors)

    @pytest.mark.parametrize(
        ('content', 'category'),
        (
            (
                _join_fixture('break', 'point() # ', 'allow-', 'debug'),
                '[DEBUG]',
            ),
            (
                _join_fixture('console.', 'log(1) # ', 'allow-', 'debug'),
                '[DEBUG]',
            ),
            (
                _join_fixture('print', "('ok') # ", 'allow-', 'debug'),
                '[DEBUG]',
            ),
            (
                _join_fixture(
                    'raise ',
                    'Not',
                    'Implemented',
                    'Error("TODO") # ',
                    'allow-',
                    'stub',
                ),
                '[STUB]',
            ),
            (
                _join_fixture('pass # TO', 'DO # ', 'stub-', 'reason'),
                '[STUB]',
            ),
            (
                _join_fixture('pass # TO', 'DO # ', 'todo-', 'reason'),
                '[STUB]',
            ),
        ),
    )
    def test_bypass_rationales_never_authorize_findings(
        self, content: str, category: str
    ) -> None:
        errors = _errors('src/demo.py', content)
        assert any(category in error for error in errors)

    def test_allow_bypass_marker_is_a_bypass_failure(self) -> None:
        errors = _errors(
            'src/demo.py', _join_fixture('# ', 'allow-', 'bypass')
        )
        assert any('[BYPASS]' in error for error in errors)

    @pytest.mark.parametrize(
        ('path', 'content'),
        (
            ('src/demo.py', _join_fixture('# no', 'qa: E501')),
            ('config.yaml', _join_fixture('# ruff: no', 'qa')),
            ('config.toml', _join_fixture('# type: ', 'ignore')),
            ('config.json', _join_fixture('"lint": "# no', 'qa"')),
            ('src/demo.js', _join_fixture('// eslint-', 'disable')),
            ('src/demo.ts', _join_fixture('@ts-', 'ignore')),
            ('src/demo.ts', _join_fixture('@ts-', 'nocheck')),
            ('src/demo.py', _join_fixture('# pragma: no ', 'cover')),
        ),
    )
    def test_source_and_configuration_suppressions_fail(
        self, path: str, content: str
    ) -> None:
        errors = _errors(path, content)
        assert any('[BYPASS]' in error for error in errors)

    @pytest.mark.parametrize('path', ('src/demo.py', 'config.yaml'))
    def test_operational_bypasses_fail(self, path: str) -> None:
        contents = (
            _join_fixture('curl https://example.invalid/script | ', 'sh'),
            _join_fixture('--no', '-verify'),
            _join_fixture('SKIP', '=1'),
            _join_fixture('continue-on-error: ', 'true'),
            _join_fixture('|| ', 'true'),
            _join_fixture('set ', '+e'),
        )
        for content in contents:
            assert any(
                '[OPERATIONAL]' in error for error in _errors(path, content)
            )

    @pytest.mark.parametrize(
        'content',
        (
            _join_fixture('# no', 'qa: cited by documentation'),
            _join_fixture('# type: ', 'ignore is discussed here'),
            _join_fixture('allow-', 'bypass is prohibited'),
        ),
    )
    def test_documentation_may_cite_suppressions(self, content: str) -> None:
        assert _errors('docs/guide.md', content) == []
        assert _errors('docs/guide.rst', content) == []
        assert _errors('docs/guide.txt', content) == []

    def test_print_requires_an_exact_file_allowlist(self) -> None:
        diff = _added_line_diff(
            'scripts/demo.py', _join_fixture('print', "('ok')")
        )
        assert any('[DEBUG]' in error for error in scan_diff(diff))
        assert scan_diff(diff, ('scripts/demo.py',)) == []
        assert scan_diff(diff, ('scripts/other.py',))

    def test_cross_boundary_change_is_not_silently_ignored(self) -> None:
        diff = (
            'diff --git a/src/demo.py b/.agents/demo.py\n'
            '--- a/src/demo.py\n'
            '+++ b/.agents/demo.py\n'
            '@@ -0,0 +1 @@\n'
            '+' + _join_fixture('break', 'point()') + '\n'
        )
        assert any('[DEBUG]' in error for error in scan_diff(diff))

    def test_external_only_change_is_ignored(self) -> None:
        diff = _added_line_diff(
            '.agents/demo.py', _join_fixture('print', "('ok')")
        )
        assert scan_diff(diff) == []

    @pytest.mark.parametrize(
        'candidate',
        (
            'scripts',
            'scripts/*.py',
            '/tmp/demo.py',
            '../demo.py',
            '.agents/demo.py',
            'scripts/missing.py',
        ),
    )
    def test_print_allowlist_rejects_non_exact_paths(
        self, candidate: str
    ) -> None:
        errors = validate_print_allowlist(
            (candidate,), ('scripts/demo.py', 'src/demo.py')
        )
        assert errors

    def test_staged_and_range_modes_produce_the_same_finding(
        self, tmp_path: Path
    ) -> None:
        _git(tmp_path, 'init')
        _git(tmp_path, 'config', 'user.email', 'quality@example.invalid')
        _git(tmp_path, 'config', 'user.name', 'Quality Gate')
        source = tmp_path / 'src' / 'demo.py'
        source.parent.mkdir(parents=True)
        source.write_text('value = 1\n', encoding='utf-8')
        _git(tmp_path, 'add', '--', 'src/demo.py')
        _git(tmp_path, 'commit', '-m', 'initial')
        base = _git(tmp_path, 'rev-parse', 'HEAD')
        source.write_text(
            'value = 1\n' + _join_fixture('break', 'point()') + '\n',
            encoding='utf-8',
        )
        _git(tmp_path, 'add', '--', 'src/demo.py')

        staged_errors = scan_diff(unified_diff(tmp_path))
        _git(tmp_path, 'commit', '-m', 'change')
        head = _git(tmp_path, 'rev-parse', 'HEAD')
        range_errors = scan_diff(unified_diff(tmp_path, f'{base}...{head}'))

        assert staged_errors == range_errors
        assert any('[DEBUG]' in error for error in range_errors)

    def test_cli_reports_git_failures_as_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)

        assert diff_sanity_main([]) == 2
        assert 'ERROR [DIFF_SANITY]' in capsys.readouterr().err
