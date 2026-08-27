"""Protect durable lifecycle and coverage invariants in hook configuration."""

from __future__ import annotations

import re

from hook_config import _HookBlock, _parse_hook_blocks

PRE_COMMIT_PATH = '.pre-commit-config.yaml'
_PINNED_SHA = re.compile(r'^[0-9a-f]{40}$')
_REV_RE = re.compile(r'^\s*rev:\s*([^\s#]+)')
_DEFAULT_INSTALL_TYPES_RE = re.compile(
    r'^default_install_hook_types:\s*\[pre-commit,\s*commit-msg,\s*pre-push\]\s*$',
    re.MULTILINE,
)
_DEFAULT_STAGES_RE = re.compile(
    r'^default_stages:\s*\[pre-commit\]\s*$', re.MULTILINE
)
_REQUIRED_HOOKS = frozenset(
    {
        'validate-commit-msg',
        'trailing-whitespace',
        'end-of-file-fixer',
        'check-yaml',
        'check-toml',
        'check-json',
        'check-merge-conflict',
        'detect-private-key',
        'lockfile-sync',
        'quality-gate-policy',
        'diff-sanity',
        'test-integrity',
        'bandit-src',
        'gitleaks',
        'ruff-check',
        'ruff-format',
        'import-linter',
        'import-cycles',
        'mypy-pre-push',
        'pytest-unit',
        'pip-audit',
    }
)
_MUTATING_HOOKS = frozenset(
    {
        'trailing-whitespace',
        'end-of-file-fixer',
        'mixed-line-ending',
        'ruff-check',
        'ruff-format',
    }
)
_REQUIRED_MIRROR_EXCLUSIONS = (
    r'\.agents/',
    r'\.claude/',
    r'\.codex/',
    r'\.opencode/',
    r'\.github/prompts/',
)
_PRE_PUSH_HOOKS = frozenset({'mypy-pre-push', 'pytest-unit', 'pip-audit'})
_COMMIT_MSG_HOOKS = frozenset({'validate-commit-msg'})
_ALWAYS_RUN_HOOKS = frozenset({'diff-sanity', *_PRE_PUSH_HOOKS})
_INDEX_ONLY_HOOKS = frozenset(
    {
        'lockfile-sync',
        'quality-gate-policy',
        'diff-sanity',
        'test-integrity',
    }
)
_FORBIDDEN_ENTRIES = (
    'harness-sync',
    '.agents/skills/local-quality-gates/scripts/',
    'git commit --no-verify',
)


def _validate_pre_commit_config(content: str) -> list[str]:
    """Return only violations that weaken durable local gate guarantees."""
    try:
        blocks = _parse_hook_blocks(content)
    except ValueError as err:
        return [str(err)]
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
        if match and not _PINNED_SHA.fullmatch(match.group(1)):
            errors.append(
                f'{PRE_COMMIT_PATH}:{line_number}: remote rev must be a 40-character SHA.'
            )
    return errors


def _validate_top_level_contract(content: str) -> list[str]:
    """Keep every installed Git hook stage explicit and reproducible."""
    errors: list[str] = []
    if not _DEFAULT_INSTALL_TYPES_RE.search(content):
        errors.append(
            'all three Git hook types must remain installed by default.'
        )
    if not _DEFAULT_STAGES_RE.search(content):
        errors.append('the default hook stage must remain pre-commit.')
    return errors


def _validate_hook_commands(blocks: dict[str, _HookBlock]) -> list[str]:
    """Reject lifecycle mutations and bypasses in local hook entries."""
    errors: list[str] = []
    for hook_id, block in blocks.items():
        entry = block.entry()
        lowered = entry.lower()
        if hook_id == 'uv-lock':
            errors.append(
                'uv-lock mutates dependency resolution; use lockfile-sync.'
            )
        errors.extend(
            f'{hook_id}: forbidden non-reproducible or bypass entry {forbidden!r}.'
            for forbidden in _FORBIDDEN_ENTRIES
            if forbidden in lowered
        )
        if re.search(r'\buv\s+sync\b', entry):
            errors.append(
                f'{hook_id}: dependency synchronization is forbidden in hooks.'
            )
        if re.search(r'\buv\s+lock\b(?!\s+--check\b)', entry):
            errors.append(
                f'{hook_id}: dependency resolution is forbidden; only uv lock --check is read-only.'
            )
        if 'uv run' in entry and not re.search(
            r'\buv\s+run\s+--locked\s+--no-sync\b', entry
        ):
            errors.append(
                f'{hook_id}: every uv run entry must begin with --locked --no-sync.'
            )
    return errors


def _validate_hook_coverage(blocks: dict[str, _HookBlock]) -> list[str]:
    """Require core gates while allowing normal maintenance of their details."""
    errors: list[str] = []
    missing = sorted(_REQUIRED_HOOKS - blocks.keys())
    if missing:
        errors.append(f'missing required hooks: {", ".join(missing)}.')
    for hook_id in _MUTATING_HOOKS:
        block = blocks.get(hook_id)
        if block is None:
            continue
        normalized_exclude = ''.join(block.value('exclude').split())
        missing_mirrors = [
            path
            for path in _REQUIRED_MIRROR_EXCLUSIONS
            if path not in normalized_exclude
        ]
        if missing_mirrors:
            errors.append(
                f'{hook_id}: generated mirrors must remain excluded: '
                f'{", ".join(missing_mirrors)}.'
            )
    gitleaks = blocks.get('gitleaks')
    if gitleaks is not None and '--redact' not in gitleaks.value('args'):
        errors.append(
            'gitleaks must retain --redact to avoid secret disclosure in logs.'
        )
    ruff_check = blocks.get('ruff-check')
    if ruff_check is not None:
        args = ruff_check.value('args')
        if '--fix' not in args or '--exit-non-zero-on-fix' not in args:
            errors.append(
                'ruff-check must retain its safe auto-fix failure mode.'
            )
    for hook_id, block in blocks.items():
        if hook_id in _PRE_PUSH_HOOKS:
            expected_stage = '[pre-push]'
        elif hook_id in _COMMIT_MSG_HOOKS:
            expected_stage = '[commit-msg]'
        else:
            continue
        if block.value('stages') != expected_stage:
            errors.append(
                f'{hook_id}: must remain in the {expected_stage} hook stage.'
            )
    for hook_id in _ALWAYS_RUN_HOOKS:
        block = blocks.get(hook_id)
        if block is not None and block.value('always_run') != 'true':
            errors.append(f'{hook_id}: must remain always_run.')
    for hook_id in _INDEX_ONLY_HOOKS:
        block = blocks.get(hook_id)
        if block is not None and block.value('pass_filenames') != 'false':
            errors.append(
                f'{hook_id}: must inspect the complete staged index, not filenames.'
            )
    return errors
