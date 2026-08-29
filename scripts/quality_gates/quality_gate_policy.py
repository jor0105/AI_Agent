"""Fail closed when the repository quality-gate contract is weakened."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from git_changes import (
    GitInspectionError,
    changed_records,
    repository_root,
    repository_snapshot,
)
from hook_policy import (
    _REQUIRED_PRINT_FILES,
    PRE_COMMIT_PATH,
    _validate_pre_commit_config,
)

_WORKFLOW_PATHS = (
    '.github/workflows/pipeline.yml',
    '.github/workflows/docs.yml',
    '.github/workflows/publish.yml',
)
_QUALITY_MODULES = (
    'scripts/check-import-cycles.py',
    'scripts/quality_gates/check_diff_sanity.py',
    'scripts/quality_gates/check_harness_projection.py',
    'scripts/quality_gates/check_lockfile_sync.py',
    'scripts/quality_gates/check_test_contracts.py',
    'scripts/quality_gates/check_test_integrity.py',
    'scripts/quality_gates/diff_sanity_policy.py',
    'scripts/quality_gates/git_changes.py',
    'scripts/quality_gates/hook_config.py',
    'scripts/quality_gates/hook_policy.py',
    'scripts/quality_gates/process_runner.py',
    'scripts/quality_gates/quality_gate_policy.py',
    'scripts/quality_gates/resolve_ci_range.py',
    'scripts/quality_gates/test_contract_ast.py',
)
_HARNESS_ENTRYPOINTS = (
    '.agents/scripts/check-max-lines.py',
    '.agents/scripts/validate-agent-protocols.py',
    '.agents/scripts/validate-commit-msg.sh',
    '.agents/skills/agents-md-author/scripts/validate_agents_md.py',
)
_REQUIRED_PATHS = (
    PRE_COMMIT_PATH,
    '.gitleaks.toml',
    'pytest.ini',
    'pyproject.toml',
    *_QUALITY_MODULES,
    *_HARNESS_ENTRYPOINTS,
    *_WORKFLOW_PATHS,
)
_POLICY_PATHS = frozenset(
    {
        *(_REQUIRED_PATHS),
        '.gitleaksignore',
    }
)
_COVERAGE_SOURCE, _COVERAGE_THRESHOLD = '--cov=src', '--cov-fail-under=85'
_GITLEAKS_ACTION = (
    'gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e'
)


def _read(snapshot: Path, path: str) -> str | None:
    candidate = snapshot / path
    if not candidate.is_file():
        return None
    try:
        return candidate.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return None


def _validate_required_paths(snapshot: Path) -> list[str]:
    return [
        f'{path} must exist and be tracked in the inspected snapshot.'
        for path in _REQUIRED_PATHS
        if not (snapshot / path).is_file()
    ]


def _validate_gitleaks_config(snapshot: Path) -> list[str]:
    content = _read(snapshot, '.gitleaks.toml')
    if content is None:
        return ['.gitleaks.toml is required and must be readable.']
    expected = (
        'title = "Create Agents AI gitleaks policy"\n\n'
        '[extend]\n'
        'useDefault = true\n'
    )
    if content != expected:
        return [
            '.gitleaks.toml must contain only the minimal default-rule policy.'
        ]
    return []


def _validate_gitleaks_ignore(snapshot: Path) -> list[str]:
    content = _read(snapshot, '.gitleaksignore')
    if content is None:
        return []
    errors: list[str] = []
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if (
            line in {'*', '**', '.*'}
            or line.endswith('/')
            or line.startswith(('/', '.agents/', 'src/'))
            or '*' in line
        ):
            errors.append(
                f'.gitleaksignore:{line_number}: broad path ignores are forbidden.'
            )
    return errors


def _validate_pytest_owner(content: str | None) -> list[str]:
    if content is None:
        return ['pytest.ini must exist and be readable.']
    errors: list[str] = []
    if not re.search(
        r'\[coverage:run\][\s\S]*?^source\s*=\s*src$', content, re.M
    ):
        errors.append('pytest.ini must own coverage source = src.')
    if not re.search(
        r'\[coverage:report\][\s\S]*?^fail_under\s*=\s*85$', content, re.M
    ):
        errors.append('pytest.ini must own coverage fail_under = 85.')
    return errors


def _validate_pyproject(content: str | None) -> list[str]:
    if content is None:
        return ['pyproject.toml must exist and be readable.']
    errors: list[str] = []
    if 'pre-commit>=4.6.2' not in content:
        errors.append('the development pre-commit lower bound must be 4.6.2.')
    if not re.search(
        r'^mypy_path\s*=\s*\["src",\s*"scripts/quality_gates"\]', content, re.M
    ):
        errors.append(
            'Mypy must search src and scripts/quality_gates explicitly.'
        )
    if not re.search(r'^explicit_package_bases\s*=\s*true$', content, re.M):
        errors.append('Mypy explicit_package_bases must remain enabled.')
    if re.search(r'^\s*ignore_missing_imports\s*=', content, re.M):
        errors.append('broad Mypy import suppression is forbidden.')
    if re.search(
        r'(?im)^\s*["\']pydocstyle(?:[<>=!~]|["\'])'
        r'|^\[tool\.pydocstyle\]',
        content,
    ):
        errors.append(
            'a separate pydocstyle dependency or gate is forbidden; Ruff owns D.'
        )
    if 'release = [' not in content or 'twine>=6.2.0,<7.0.0' not in content:
        errors.append(
            'the locked release dependency group must provide Twine.'
        )
    select = re.search(
        r'\[tool\.ruff\.lint\][\s\S]*?^select\s*=\s*\[([\s\S]*?)^\]',
        content,
        re.M,
    )
    selected = '' if select is None else select.group(1)
    selected_rules = set(re.findall(r'["\']([A-Z][A-Z0-9]*)["\']', selected))
    errors.extend(
        f'Ruff must own the {rule} rule family.'
        for rule in ('D', 'T201', 'C901')
        if rule not in selected_rules
    )
    if 'S' in selected_rules:
        errors.append(
            'Ruff security S rules must remain disabled; Bandit owns them.'
        )
    return errors


def _validate_coverage_duplicates(contents: Sequence[str | None]) -> list[str]:
    errors: list[str] = []
    for index, content in enumerate(contents):
        if content is None:
            continue
        if _COVERAGE_SOURCE in content or _COVERAGE_THRESHOLD in content:
            errors.append(
                f'coverage source/threshold is duplicated outside pytest.ini '
                f'(policy input {index}).'
            )
    return errors


def _validate_pipeline(content: str | None) -> list[str]:
    if content is None:
        return ['pipeline.yml must exist and be readable.']
    normalized = re.sub(r'\s+', ' ', re.sub(r'\\\s*\n\s*', ' ', content))
    required = (
        'uv sync --locked',
        'uv lock --check',
        'uv run --locked --no-sync bandit',
        'uv run --locked --no-sync pip-audit --timeout 60',
        'uv run --locked --no-sync pre-commit run --all-files '
        '--show-diff-on-failure',
        'uv run --locked --no-sync bandit -c pyproject.toml -r src -ll',
        'mypy src --pretty',
        'mypy tests scripts --disable-error-code no-untyped-def --pretty',
        'check_diff_sanity.py --range',
        'check_test_integrity.py --range',
        'check_test_contracts.py --revision',
        'quality_gate_policy.py --revision',
        'check_harness_projection.py --revision',
        _GITLEAKS_ACTION,
        'GITLEAKS_VERSION: "8.30.0"',
        'GITLEAKS_CONFIG: ".gitleaks.toml"',
        'GITLEAKS_ENABLE_COMMENTS: "false"',
        'GITLEAKS_ENABLE_UPLOAD_ARTIFACT: "false"',
    )
    errors = [
        f'pipeline.yml is missing required command or setting: {item}'
        for item in required
        if item not in normalized
    ]
    expected_allowlist = (
        'diff_allowlist=( ' + ' '.join(sorted(_REQUIRED_PRINT_FILES)) + ' )'
    )
    if expected_allowlist not in normalized:
        errors.append(
            'pipeline.yml must define the exact diff-sanity print allowlist.'
        )
    if '"${diff_allowlist[@]/#/--allow-print-file=}"' not in content:
        errors.append(
            'pipeline.yml must pass the complete diff-sanity print allowlist.'
        )
    if 'GITLEAKS_LICENSE' in content:
        errors.append('the personal Gitleaks job must not define a license.')
    if re.search(r'\buv run\b(?!\s+--locked\s+--no-sync)', content):
        errors.append(
            'every pipeline Python tool must use locked no-sync execution.'
        )
    if re.search(r'\buv sync\b(?!\s+--locked)', content):
        errors.append(
            'every pipeline environment synchronization must be locked.'
        )
    if 'secret-scan:' not in content or 'fetch-depth: 0' not in content:
        errors.append(
            'the pipeline must retain a full-history, non-matrix secret scan.'
        )
    if 'contents: read' not in content:
        errors.append(
            'the pipeline must retain read-only repository permissions.'
        )
    return errors


def _validate_docs(content: str | None) -> list[str]:
    if content is None:
        return ['docs.yml must exist and be readable.']
    return [
        f'docs.yml is missing required command: {item}'
        for item in (
            'uv sync --locked',
            'uv run --locked --no-sync mkdocs build --strict',
        )
        if item not in content
    ]


def _validate_publish(content: str | None) -> list[str]:
    if content is None:
        return ['publish.yml must exist and be readable.']
    required = (
        'uv sync --locked',
        'uv run --locked --no-sync bandit',
        'uv run --locked --no-sync pip-audit --timeout 60',
        'uv run --locked --no-sync twine check',
        'uv build',
    )
    errors = [
        f'publish.yml is missing required command: {item}'
        for item in required
        if item not in content
    ]
    if ' --with ' in content or '--with twine' in content:
        errors.append(
            'publish.yml must use the locked release dependency group.'
        )
    if 'uv sync --locked --no-dev --group release' not in content:
        errors.append(
            'publish.yml must install the locked release dependency group.'
        )
    return errors


def _validate_shell_gate(snapshot: Path, pre_commit: str | None) -> list[str]:
    if pre_commit is None:
        return []
    shell_paths = [
        path
        for path in snapshot.rglob('*')
        if path.is_file()
        and path.suffix.lower() in {'.sh', '.bash'}
        and not str(path.relative_to(snapshot)).startswith(
            (
                '.git/',
                '.venv/',
                'site/',
                'dist/',
                '.agents/',
                '.claude/',
                '.codex/',
                '.opencode/',
                '.github/prompts/',
            )
        )
    ]
    if shell_paths and '- id: shell-syntax' not in pre_commit:
        return [
            'tracked product shell files require a staged-content shell-syntax hook.'
        ]
    return []


def validate_quality_policy(snapshot: Path) -> list[str]:
    """Return violations for one materialized staged or revision snapshot."""
    errors = _validate_required_paths(snapshot)
    texts = {path: _read(snapshot, path) for path in _POLICY_PATHS}
    pre_commit = texts[PRE_COMMIT_PATH]
    if pre_commit is not None:
        errors.extend(_validate_pre_commit_config(pre_commit))
    errors.extend(_validate_gitleaks_config(snapshot))
    errors.extend(_validate_gitleaks_ignore(snapshot))
    errors.extend(_validate_pytest_owner(texts['pytest.ini']))
    errors.extend(_validate_pyproject(texts['pyproject.toml']))
    errors.extend(
        _validate_coverage_duplicates(
            [pre_commit, *[texts[path] for path in _WORKFLOW_PATHS]]
        )
    )
    errors.extend(_validate_pipeline(texts[_WORKFLOW_PATHS[0]]))
    errors.extend(_validate_docs(texts[_WORKFLOW_PATHS[1]]))
    errors.extend(_validate_publish(texts[_WORKFLOW_PATHS[2]]))
    errors.extend(_validate_shell_gate(snapshot, pre_commit))
    return errors


def _is_relevant(path: str) -> bool:
    return path in _POLICY_PATHS or path.startswith('scripts/quality_gates/')


def main(argv: Sequence[str] | None = None) -> int:
    """Validate staged policy inputs or one exact checked-out revision."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', metavar='REV')
    args = parser.parse_args(argv)
    try:
        root = repository_root()
        if args.revision:
            with repository_snapshot(
                root, args.revision, scope='repository'
            ) as snapshot:
                errors = validate_quality_policy(snapshot)
        else:
            changes = changed_records(root)
            paths = {
                path
                for change in changes
                for path in (change.old_path, change.new_path)
                if path is not None
            }
            if not any(_is_relevant(path) for path in paths):
                print('SKIP [QUALITY_GATE_POLICY]: No policy inputs changed.')
                return 0
            with repository_snapshot(root, scope='repository') as snapshot:
                errors = validate_quality_policy(snapshot)
    except GitInspectionError as git_error:
        print(f'ERROR [QUALITY_GATE_POLICY]: {git_error}', file=sys.stderr)
        return 2
    if errors:
        print(
            'FAIL [QUALITY_GATE_POLICY]: Quality-gate policy is invalid:',
            file=sys.stderr,
        )
        for violation in errors:
            print(f'  • {violation}', file=sys.stderr)
        return 1
    print('PASS [QUALITY_GATE_POLICY]: Quality-gate policy is intact.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
