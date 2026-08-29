"""Protect durable lifecycle and coverage invariants in hook configuration."""

from __future__ import annotations

import re

from hook_config import _HookBlock, _parse_hook_blocks

PRE_COMMIT_PATH = '.pre-commit-config.yaml'

# fmt: off


def _join(*parts: str) -> str:
    """Build policy tokens without creating unsafe diff fixtures."""
    return ''.join(parts)


_PINNED_SHA = re.compile(r'^[0-9a-f]{40}$')
_REV_RE = re.compile(r'^\s*rev:\s*([\s\S]+?)\s*(?:#.*)?$')
_MINIMUM_VERSION = '4.6.2'
_UV_RUN = _join('uv', ' run')
_UV_SYNC = _join('uv', ' sync')
_UV_LOCK = _join('uv', ' lock')
_NO_VERIFY = _join('--no', '-verify')
_UPGRADE = _join('--', 'upgrade')
_COVERAGE_SOURCE = _join('--cov', '=src')
_COVERAGE_THRESHOLD = _join('--cov-fail', '-under=85')
_HARNESS_SYNC = _join('harness', '-sync')

_DEFAULT_INSTALL_TYPES_RE = re.compile(
    r'^default_install_hook_types:\s*'
    r'\[pre-commit,\s*commit-msg,\s*pre-push\]\s*$',
    re.MULTILINE,
)
_DEFAULT_STAGES_RE = re.compile(
    r'^default_stages:\s*\[pre-commit\]\s*$', re.MULTILINE
)
_ROOT_EXCLUDE_RE = re.compile(
    r'^exclude:\s*\|\s*$\n(?P<body>(?:^[ \t]+.*(?:\n|$))*)',
    re.MULTILINE,
)

_REQUIRED_HOOKS = frozenset({'validate-commit-msg', 'trailing-whitespace', 'end-of-file-fixer', 'mixed-line-ending', 'check-yaml', 'check-toml', 'check-json', 'check-merge-conflict', 'debug-statements', 'check-ast', 'check-added-large-files', 'check-case-conflict', 'detect-private-key', 'check-executables-have-shebangs', 'check-shebang-scripts-are-executable', 'check-symlinks', 'destroyed-symlinks', 'forbid-submodules', 'name-tests-test', 'lockfile-sync', 'quality-gate-policy', 'validate-agents-md', 'validate-agent-protocols', 'check-max-lines', 'check-harness-projection', 'diff-sanity', 'test-contracts', 'test-integrity', 'bandit-src', 'gitleaks', 'zizmor', 'ruff-check', 'ruff-format', 'mdformat', 'yamllint', 'actionlint', 'codespell', 'import-linter', 'import-cycles', 'mypy-pre-push', 'mypy-supporting', 'pytest-unit', 'pip-audit', 'check-harness-sync'})
_MUTATING_HOOKS = frozenset({'trailing-whitespace', 'end-of-file-fixer', 'mixed-line-ending', 'ruff-check', 'ruff-format', 'mdformat'})
_GLOBAL_RETAINED_EXCLUSIONS = ('site/', 'dist/', r'\.benchmarks/', r'\.venv/')
_EXTERNAL_RETAINED_EXCLUSIONS = (r'\.agents/', r'\.claude/', r'\.codex/', r'\.opencode/', r'\.github/prompts/')
_PRE_PUSH_HOOKS = frozenset({'mypy-pre-push', 'mypy-supporting', 'pytest-unit', 'pip-audit'})
_COMMIT_MSG_HOOKS = frozenset({'validate-commit-msg'})
_MANUAL_HOOKS = frozenset({'check-harness-sync'})
_COMPLETE_INDEX_HOOKS = frozenset({'lockfile-sync', 'quality-gate-policy', 'check-max-lines', 'check-harness-projection', 'diff-sanity', 'test-contracts', 'test-integrity', 'gitleaks', 'mypy-pre-push', 'mypy-supporting', 'pytest-unit', 'pip-audit'})
_REQUIRED_PRINT_FILES = frozenset({'scripts/check-import-cycles.py', 'scripts/quality_gates/check_diff_sanity.py', 'scripts/quality_gates/check_harness_projection.py', 'scripts/quality_gates/check_lockfile_sync.py', 'scripts/quality_gates/check_test_contracts.py', 'scripts/quality_gates/check_test_integrity.py', 'scripts/quality_gates/quality_gate_policy.py', 'scripts/quality_gates/resolve_ci_range.py', 'src/createagents/presentation/cli/ui/terminal_renderer.py'})
_FORBIDDEN_ENTRIES = (_NO_VERIFY, '.agents/skills/local-quality-gates/scripts/', 'pydocstyle', 'pip install', 'poetry add', 'poetry update', 'uv add ', 'uv remove ', 'uv pip install')
_EXACT_LOCAL_ENTRIES = {'validate-commit-msg': 'bash .agents/scripts/validate-commit-msg.sh', 'lockfile-sync': 'uv run --locked --no-sync python scripts/quality_gates/check_lockfile_sync.py', 'quality-gate-policy': 'uv run --locked --no-sync python scripts/quality_gates/quality_gate_policy.py', 'check-harness-projection': 'uv run --locked --no-sync python scripts/quality_gates/check_harness_projection.py', 'validate-agents-md': 'uv run --locked --no-sync python .agents/skills/agents-md-author/scripts/validate_agents_md.py', 'validate-agent-protocols': 'uv run --locked --no-sync python .agents/scripts/validate-agent-protocols.py', 'check-max-lines': 'uv run --locked --no-sync python .agents/scripts/check-max-lines.py', 'diff-sanity': 'uv run --locked --no-sync python scripts/quality_gates/check_diff_sanity.py', 'test-contracts': 'uv run --locked --no-sync python scripts/quality_gates/check_test_contracts.py', 'test-integrity': 'uv run --locked --no-sync python scripts/quality_gates/check_test_integrity.py', 'bandit-src': 'uv run --locked --no-sync bandit -q -c pyproject.toml -ll', 'import-linter': 'uv run --locked --no-sync lint-imports', 'import-cycles': 'uv run --locked --no-sync python scripts/check-import-cycles.py', 'mypy-pre-push': 'uv run --locked --no-sync mypy src --pretty', 'mypy-supporting': 'uv run --locked --no-sync mypy tests scripts --disable-error-code no-untyped-def --pretty', 'pytest-unit': 'uv run --locked --no-sync pytest -q -m "not integration and not slow" --cov', 'pip-audit': 'uv run --locked --no-sync pip-audit --timeout 60', 'check-harness-sync': 'uv run --locked --no-sync harness-sync --check'}
# fmt: on


def _compact(value: str) -> str:
    return re.sub(r'\s+', '', value)


def _tokens(value: str) -> tuple[str, ...]:
    cleaned = re.sub(r'[\[\],"\']', ' ', value)
    return tuple(token for token in cleaned.split() if token)


def _validate_pre_commit_config(content: str) -> list[str]:
    """Return violations that weaken durable local gate guarantees."""
    try:
        blocks = _parse_hook_blocks(content)
    except ValueError as error:
        return [str(error)]
    errors = _validate_pinned_revisions(content)
    errors.extend(_validate_top_level_contract(content))
    errors.extend(_validate_hook_commands(blocks))
    errors.extend(_validate_hook_coverage(blocks))
    return errors


def _validate_pinned_revisions(content: str) -> list[str]:
    """Require immutable full commit SHAs for every remote hook source."""
    errors: list[str] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        match = _REV_RE.match(line)
        if match and not _PINNED_SHA.fullmatch(match.group(1).strip()):
            errors.append(
                f'{PRE_COMMIT_PATH}:{line_number}: remote rev must be a '
                '40-character SHA.'
            )
    return errors


def _validate_top_level_contract(content: str) -> list[str]:
    """Keep installed hook stages and the global path boundary explicit."""
    errors: list[str] = []
    minimum = re.search(
        r'^minimum_pre_commit_version:\s*["\']?([^"\'\s]+)',
        content,
        re.MULTILINE,
    )
    if minimum is None or minimum.group(1) != _MINIMUM_VERSION:
        errors.append(
            'minimum_pre_commit_version must remain the locked 4.6.2.'
        )
    if not _DEFAULT_INSTALL_TYPES_RE.search(content):
        errors.append(
            'all three Git hook types must remain installed by default.'
        )
    if not _DEFAULT_STAGES_RE.search(content):
        errors.append('the default hook stage must remain pre-commit.')
    if re.search(r'^default_language_version:', content, re.MULTILINE):
        errors.append('the global Python hook-environment pin is forbidden.')
    match = _ROOT_EXCLUDE_RE.search(content)
    exclude = '' if match is None else _compact(match.group('body'))
    errors.extend(
        f'global pre-commit exclusion is missing: {marker}'
        for marker in (
            *_GLOBAL_RETAINED_EXCLUSIONS,
            *_EXTERNAL_RETAINED_EXCLUSIONS,
        )
        if marker not in exclude
    )
    return errors


def _validate_hook_commands(blocks: dict[str, _HookBlock]) -> list[str]:
    """Reject lifecycle mutations and bypasses in local hook entries."""
    errors: list[str] = []
    uv_run_pattern = re.compile(
        rf'\b{re.escape(_UV_RUN)}\s+--locked\s+--no-sync\b'
    )
    for hook_id, block in blocks.items():
        entry = block.entry()
        lowered = entry.casefold()
        if hook_id == 'uv-lock':
            errors.append(
                'uv-lock mutates dependency resolution; use lockfile-sync.'
            )
        if _HARNESS_SYNC in lowered and hook_id != 'check-harness-sync':
            errors.append(
                'harness-sync is permitted only in the manual check-harness-sync hook.'
            )
        errors.extend(
            f'{hook_id}: forbidden non-reproducible or bypass entry '
            f'{forbidden!r}.'
            for forbidden in _FORBIDDEN_ENTRIES
            if forbidden.casefold() in lowered
        )
        if _UV_SYNC in lowered:
            errors.append(
                f'{hook_id}: dependency synchronization is forbidden in hooks.'
            )
        if re.search(rf'\b{re.escape(_UV_LOCK)}\b(?!\s+--check\b)', entry):
            errors.append(
                f'{hook_id}: dependency resolution is forbidden; only the '
                'read-only lock check is allowed.'
            )
        if _UV_RUN in lowered and not uv_run_pattern.search(entry):
            errors.append(
                f'{hook_id}: every uv run entry must begin with the locked '
                'no-sync flags.'
            )
        if _UPGRADE in lowered:
            errors.append(
                f'{hook_id}: dependency upgrade flags are forbidden.'
            )
    return errors


def _validate_required_hooks(blocks: dict[str, _HookBlock]) -> list[str]:
    """Return errors for a missing hook or an unexpected roster size."""
    missing = sorted(_REQUIRED_HOOKS - blocks.keys())
    errors = (
        [f'missing required hooks: {", ".join(missing)}.'] if missing else []
    )
    if len(blocks) != 44:
        errors.append(
            f'hook roster must contain 44 entries; found {len(blocks)}.'
        )
    return errors


def _validate_mutating_hook_exclusions(
    blocks: dict[str, _HookBlock],
) -> list[str]:
    """Keep generated mirrors outside every mutating hook."""
    errors: list[str] = []
    for hook_id in _MUTATING_HOOKS:
        block = blocks.get(hook_id)
        if block is None:
            continue
        normalized_exclude = _compact(block.value('exclude'))
        missing_mirrors = [
            path
            for path in _EXTERNAL_RETAINED_EXCLUSIONS
            if path not in normalized_exclude
        ]
        if missing_mirrors:
            errors.append(
                f'{hook_id}: generated mirrors must remain excluded: '
                f'{", ".join(missing_mirrors)}.'
            )
    return errors


def _validate_gitleaks(blocks: dict[str, _HookBlock]) -> list[str]:
    """Require one redacted, complete-index secret scan."""
    block = blocks.get('gitleaks')
    if block is None:
        return []
    expected = ('--redact', '--config=.gitleaks.toml')
    errors: list[str] = []
    if _tokens(block.value('args')) != expected:
        errors.append(
            'gitleaks must use exactly --redact and --config=.gitleaks.toml.'
        )
    if block.value('pass_filenames') != 'false':
        errors.append('gitleaks must inspect the complete tracked repository.')
    if block.value('always_run') != 'true':
        errors.append('gitleaks must remain always_run.')
    return errors


def _validate_ruff_autofix(blocks: dict[str, _HookBlock]) -> list[str]:
    """Require Ruff's safe and visible automatic-fix behavior."""
    ruff_check = blocks.get('ruff-check')
    if ruff_check is None:
        return []
    args = _tokens(ruff_check.value('args'))
    if '--fix' in args and '--exit-non-zero-on-fix' in args:
        return []
    return ['ruff-check must retain its safe auto-fix failure mode.']


def _validate_explicit_stages(blocks: dict[str, _HookBlock]) -> list[str]:
    """Keep pre-push, commit-message, and manual hooks on owned stages."""
    errors: list[str] = []
    expected = {
        **dict.fromkeys(_PRE_PUSH_HOOKS, '[pre-push]'),
        **dict.fromkeys(_COMMIT_MSG_HOOKS, '[commit-msg]'),
        **dict.fromkeys(_MANUAL_HOOKS, '[manual]'),
    }
    for hook_id, block in blocks.items():
        expected_stage = expected.get(hook_id)
        if (
            expected_stage is not None
            and block.value('stages') != expected_stage
        ):
            errors.append(
                f'{hook_id}: must remain in the {expected_stage} hook stage.'
            )
        if expected_stage is None and block.value('stages'):
            errors.append(
                f'{hook_id}: unexpected explicit hook stage '
                f'{block.value("stages")!r}.'
            )
    return errors


def _validate_roster_counts(blocks: dict[str, _HookBlock]) -> list[str]:
    """Ensure the documented four-stage roster cannot silently drift."""
    counts = {'pre-commit': 0, 'pre-push': 0, 'commit-msg': 0, 'manual': 0}
    for block in blocks.values():
        stage = block.value('stages').strip('[]') or 'pre-commit'
        if stage in counts:
            counts[stage] += 1
    expected = {
        'pre-commit': 38,
        'pre-push': 4,
        'commit-msg': 1,
        'manual': 1,
    }
    return [
        f'{stage} roster must contain {expected[stage]} entries; found {counts[stage]}.'
        for stage in expected
        if counts[stage] != expected[stage]
    ]


def _validate_complete_index_hooks(
    blocks: dict[str, _HookBlock],
) -> list[str]:
    """Require complete-index hooks to own their invocation and selection."""
    errors: list[str] = []
    for hook_id in _COMPLETE_INDEX_HOOKS:
        block = blocks.get(hook_id)
        if block is None:
            continue
        if block.value('pass_filenames') != 'false':
            errors.append(f'{hook_id}: must set pass_filenames: false.')
        if block.value('always_run') != 'true':
            errors.append(f'{hook_id}: must remain always_run.')
        if block.value('files'):
            errors.append(
                f'{hook_id}: complete-index hooks cannot use files:.'
            )
    return errors


def _validate_exact_entries(blocks: dict[str, _HookBlock]) -> list[str]:
    return [
        f'{hook_id}: entry must remain {expected!r}.'
        for hook_id, expected in _EXACT_LOCAL_ENTRIES.items()
        if (block := blocks.get(hook_id)) is not None
        and block.entry() != expected
    ]


def _validate_specific_commands(blocks: dict[str, _HookBlock]) -> list[str]:
    """Protect the deliberately split ownership of local tools."""
    errors = _validate_exact_entries(blocks)
    agents = blocks.get('validate-agents-md')
    if agents is not None and _tokens(agents.value('args')) != (
        '--strict-governance',
    ):
        errors.append('validate-agents-md must enable strict governance.')
    if agents is not None and agents.value('files') != r'^AGENTS\.md$':
        errors.append(
            'validate-agents-md must target only the root AGENTS.md.'
        )

    max_lines = blocks.get('check-max-lines')
    if max_lines is not None and _tokens(max_lines.value('args')) != (
        'src',
        'tests',
        'scripts',
    ):
        errors.append(
            'check-max-lines must select exactly src, tests, and scripts.'
        )

    codespell = blocks.get('codespell')
    expected_codespell = r'^(?:src|tests|scripts)/.*\.(?:py|pyi|pyw|sh|bash)$'
    if codespell is not None and _compact(
        codespell.value('files')
    ) != _compact(expected_codespell):
        errors.append(
            'codespell must cover the declared executable-code regex.'
        )

    bandit = blocks.get('bandit-src')
    if bandit is not None and '-ll' not in _tokens(bandit.entry()):
        errors.append('bandit-src must use the aligned -ll severity profile.')

    pip_audit = blocks.get('pip-audit')
    if pip_audit is not None and not re.search(
        r'\bpip-audit\b.*--timeout\s+60\b', pip_audit.entry()
    ):
        errors.append('pip-audit must use --timeout 60.')

    diff_sanity = blocks.get('diff-sanity')
    if diff_sanity is not None:
        allowed = set(
            re.findall(
                r'--allow-print-file=([^\s,\]]+)',
                diff_sanity.value('args'),
            )
        )
        if allowed != _REQUIRED_PRINT_FILES:
            errors.append(
                'diff-sanity must use the exact repository print allowlist.'
            )

    harness_sync = blocks.get('check-harness-sync')
    if harness_sync is not None and _tokens(harness_sync.value('args')):
        errors.append('check-harness-sync must not add command arguments.')

    return errors


def _validate_coverage_owner(blocks: dict[str, _HookBlock]) -> list[str]:
    """Keep pytest.ini as the only measurement threshold owner."""
    pytest_hook = blocks.get('pytest-unit')
    if pytest_hook is None:
        return []
    entry = pytest_hook.entry()
    errors: list[str] = []
    if not re.search(r'(?<![=\w])--cov(?![=\w])', entry):
        errors.append('pytest-unit must measure coverage with the --cov flag.')
    if _COVERAGE_SOURCE in entry or _COVERAGE_THRESHOLD in entry:
        errors.append(
            'pytest-unit must not duplicate pytest.ini coverage ownership.'
        )
    return errors


def _validate_hook_coverage(blocks: dict[str, _HookBlock]) -> list[str]:
    """Require the complete, four-stage quality-gate contract."""
    return [
        *_validate_required_hooks(blocks),
        *_validate_roster_counts(blocks),
        *_validate_mutating_hook_exclusions(blocks),
        *_validate_gitleaks(blocks),
        *_validate_ruff_autofix(blocks),
        *_validate_explicit_stages(blocks),
        *_validate_complete_index_hooks(blocks),
        *_validate_specific_commands(blocks),
        *_validate_coverage_owner(blocks),
    ]
