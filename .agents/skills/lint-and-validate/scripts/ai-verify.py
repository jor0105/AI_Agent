#!/usr/bin/env python3
"""Harness unico de verificacao do repo."""

from __future__ import annotations

import argparse
import contextlib
import fnmatch
import json
import re
import shlex
import subprocess  # nosec B404
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_ROOT.parent
AI_VERIFY_SCHEMA_VERSION = '1.0.0'
PROFILE_PRIORITY = {
    'quick': 1,
    'standard': 2,
    'high-risk': 3,
    'ui-flow': 4,
    'security-touch': 5,
}
TOP_LEVEL_STATUSES = {'passed', 'failed', 'skipped', 'external_failure'}
GATE_STATUSES = {'passed', 'failed', 'skipped', 'external_failure'}
CLASSIFICATIONS = {'code', 'environment', 'not_configured', 'not_applicable'}
VERIFY_HOOK_STAGES = ('pre-commit', 'pre-push')


@dataclass
class PrecommitHookResult:
    hook_id: str
    label: str
    status: str
    classification: str
    exit_code: int | None
    details: str
    modified_files: bool
    duration_ms: int


@dataclass(frozen=True)
class GateSpec:
    name: str
    label: str
    command: str
    blocking: bool
    timeout_ms: int
    script: str | None = None
    allow_missing: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Executa verificacao repo-native com perfis declarativos.',
    )
    parser.add_argument(
        '--mode',
        choices=['precommit', 'gates'],
        default='precommit',
    )
    parser.add_argument(
        '--profile',
        default='auto',
    )
    parser.add_argument('--session-dir', default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--changed-file', action='append', default=[])
    parser.add_argument('--skip-defaults', action='store_true')
    parser.add_argument(
        '--gate',
        action='append',
        default=[],
        help='Formato: gateId|Label|blocking|command',
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding='utf-8'))
    return result if isinstance(result, dict) else {}


def require_mapping(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f'{field} must be an object in extension config')
    return value


def merge_escalation_rules(
    base: dict[str, list[dict[str, Any]]],
    extra: object,
) -> None:
    rules_by_flag = require_mapping(extra, field='escalationRules')
    for flag_name in (
        'reviewRequired',
        'securityRequired',
        'testerRecommended',
    ):
        rules = rules_by_flag.get(flag_name, [])
        if not isinstance(rules, list):
            raise TypeError(
                f'escalationRules.{flag_name} must be a list in extension config'
            )
        base.setdefault(flag_name, []).extend(rules)


def merge_extension_config(
    config: dict[str, Any],
    extension: dict[str, Any],
    extension_path: Path,
) -> None:
    if extension.get('schemaVersion') != '1.0.0':
        raise ValueError(
            f'{extension_path}: unsupported ai-verify extension schemaVersion'
        )

    profiles = require_mapping(
        extension.get('profiles', {}),
        field='profiles',
    )
    for profile_id, raw_profile_config in profiles.items():
        profile_config = require_mapping(
            raw_profile_config,
            field=f'profiles.{profile_id}',
        )
        if profile_id in config['profiles']:
            raise ValueError(
                f'{extension_path}: duplicate ai:verify profile {profile_id!r}'
            )
        priority = profile_config.get('priority')
        if not isinstance(priority, int):
            raise TypeError(
                f'{extension_path}: profile {profile_id!r} requires integer '
                'priority'
            )
        config['profiles'][profile_id] = profile_config
        PROFILE_PRIORITY[profile_id] = priority

    gates = require_mapping(extension.get('gates', {}), field='gates')
    for gate_id, raw_gate_config in gates.items():
        gate_config = require_mapping(
            raw_gate_config,
            field=f'gates.{gate_id}',
        )
        if gate_id in config['gates']:
            raise ValueError(
                f'{extension_path}: duplicate ai:verify gate {gate_id!r}'
            )
        config['gates'][gate_id] = gate_config

    path_rules = extension.get('pathRules', [])
    if not isinstance(path_rules, list):
        raise TypeError(f'{extension_path}: pathRules must be a list')
    config['pathRules'].extend(path_rules)

    merge_escalation_rules(
        config['escalationRules'],
        extension.get('escalationRules', {}),
    )


def load_verification_config() -> dict[str, Any]:
    profiles_config = load_json(
        SKILL_ROOT / 'assets' / 'verification-profiles.json'
    )
    path_rules = load_json(SKILL_ROOT / 'assets' / 'path-rules.json')['rules']
    escalation_rules = load_json(
        SKILL_ROOT / 'assets' / 'escalation-rules.json'
    )

    config: dict[str, Any] = {
        'gates': dict(profiles_config.get('gates', {})),
        'profiles': dict(profiles_config.get('profiles', {})),
        'pathRules': list(path_rules),
        'escalationRules': {
            'reviewRequired': list(escalation_rules.get('reviewRequired', [])),
            'securityRequired': list(
                escalation_rules.get('securityRequired', [])
            ),
            'testerRecommended': list(
                escalation_rules.get('testerRecommended', [])
            ),
        },
    }

    for profile_id, profile_config in config['profiles'].items():
        if profile_id not in PROFILE_PRIORITY:
            PROFILE_PRIORITY[profile_id] = int(
                profile_config.get('priority', len(PROFILE_PRIORITY) + 1)
            )

    extension_paths = sorted(
        (REPO_ROOT / '.agents' / 'skills').glob(
            '*/assets/ai-verify-extension.json'
        )
    )
    for extension_path in extension_paths:
        merge_extension_config(
            config, load_json(extension_path), extension_path
        )

    return config


def normalize_repo_path(raw_path: str) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        path = path.resolve().relative_to(REPO_ROOT)
    normalized = path.as_posix()
    if normalized.startswith('./'):
        normalized = normalized[2:]
    return normalized


def load_package_scripts() -> dict[str, str]:
    package_json = REPO_ROOT / 'package.json'
    if not package_json.exists():
        return {}
    payload = load_json(package_json)
    scripts = payload.get('scripts', {})
    if not isinstance(scripts, dict):
        return {}
    return {str(name): str(command) for name, command in scripts.items()}


def load_review_session_changed_files(session_dir: str | None) -> list[str]:
    if not session_dir:
        return []
    session_path = (
        REPO_ROOT / session_dir / 'artifacts' / 'review-session.json'
    )
    if not session_path.exists():
        return []
    payload = load_json(session_path)
    changed_files = payload.get('changedFiles', [])
    if not isinstance(changed_files, list):
        return []
    return sorted(
        normalize_repo_path(item)
        for item in changed_files
        if isinstance(item, str)
    )


def run_git_paths(command: list[str]) -> set[str]:
    result = subprocess.run(  # nosec B603
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {
        normalize_repo_path(line.strip())
        for line in result.stdout.splitlines()
        if line.strip()
    }


def detect_changed_files(
    cli_changed_files: list[str], session_dir: str | None
) -> list[str]:
    if cli_changed_files:
        return sorted(
            {normalize_repo_path(item) for item in cli_changed_files}
        )

    session_changed = load_review_session_changed_files(session_dir)
    if session_changed:
        return session_changed

    changed = set()
    changed |= run_git_paths(['git', 'diff', '--name-only', '--cached'])
    changed |= run_git_paths(['git', 'diff', '--name-only'])
    changed |= run_git_paths(
        ['git', 'ls-files', '--others', '--exclude-standard']
    )
    return sorted(changed)


def path_matches(pattern: str, changed_file: str) -> bool:
    return fnmatch.fnmatch(changed_file, pattern)


def strongest_profile(profiles: list[str]) -> str | None:
    if not profiles:
        return None
    return max(profiles, key=lambda profile: PROFILE_PRIORITY.get(profile, 0))


def _matched_profile_rules(
    changed_files: list[str],
    path_rules: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    matched_profiles: list[str] = []
    matched_reasons: list[str] = []
    for changed_file in changed_files:
        for rule in path_rules:
            pattern = str(rule.get('pattern', ''))
            profile = rule.get('profile')
            if (
                pattern
                and isinstance(profile, str)
                and path_matches(pattern, changed_file)
            ):
                matched_profiles.append(profile)
                matched_reasons.append(
                    str(rule.get('reason', f'Matched {pattern}.'))
                )
    return matched_profiles, matched_reasons


def _resolve_auto_profile(
    detected_profile: str | None,
    changed_files: list[str],
    matched_reasons: list[str],
) -> tuple[str, str]:
    if detected_profile:
        return detected_profile, '; '.join(dict.fromkeys(matched_reasons))
    if not changed_files:
        return (
            'standard',
            'Nenhum arquivo alterado detectado; usando perfil standard por default.',
        )
    return (
        'standard',
        'Nenhuma regra especial disparou; usando perfil standard.',
    )


def resolve_effective_profile(
    requested_profile: str,
    changed_files: list[str],
    path_rules: list[dict[str, Any]],
) -> tuple[str, str]:
    matched_profiles, matched_reasons = _matched_profile_rules(
        changed_files, path_rules
    )
    detected_profile = strongest_profile(matched_profiles)
    if requested_profile == 'auto':
        return _resolve_auto_profile(
            detected_profile,
            changed_files,
            matched_reasons,
        )

    if detected_profile and PROFILE_PRIORITY.get(
        detected_profile, 0
    ) > PROFILE_PRIORITY.get(requested_profile, 0):
        return (
            detected_profile,
            '; '.join(
                dict.fromkeys(
                    [
                        *matched_reasons,
                        f"Perfil pedido '{requested_profile}' foi elevado para '{detected_profile}'.",
                    ]
                ),
            ),
        )
    return (
        requested_profile,
        f"Perfil '{requested_profile}' solicitado explicitamente.",
    )


def collect_escalation_reasons(
    changed_files: list[str],
    effective_profile: str,
    escalation_rules: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        'reviewRequired': False,
        'securityRequired': False,
        'testerRecommended': False,
    }
    reasons: list[str] = []

    def apply_rules(flag_name: str, rules: list[dict[str, Any]]) -> None:
        for rule in rules:
            profile = rule.get('profile')
            pattern = rule.get('pattern')
            reason = str(rule.get('reason', '')).strip()
            if isinstance(profile, str) and profile == effective_profile:
                result[flag_name] = True
                if reason:
                    reasons.append(reason)
            if isinstance(pattern, str) and any(
                path_matches(pattern, item) for item in changed_files
            ):
                result[flag_name] = True
                if reason:
                    reasons.append(reason)

    apply_rules('reviewRequired', escalation_rules.get('reviewRequired', []))
    apply_rules(
        'securityRequired', escalation_rules.get('securityRequired', [])
    )
    apply_rules(
        'testerRecommended', escalation_rules.get('testerRecommended', [])
    )
    result['reasons'] = list(dict.fromkeys(reasons))
    return result


def parse_custom_gate(raw_gate: str) -> GateSpec:
    parts = [item.strip() for item in raw_gate.split('|', 3)]
    if len(parts) != 4:
        raise ValueError(
            'gate spec must use format gateId|Label|blocking|command'
        )
    gate_name, label, blocking_raw, command = parts
    if blocking_raw.lower() not in {'true', 'false'}:
        raise ValueError(
            f'gate {gate_name!r} has invalid blocking flag {blocking_raw!r}'
        )
    if not gate_name or not label or not command:
        raise ValueError('gate spec cannot contain empty values')
    return GateSpec(
        name=gate_name,
        label=label,
        command=command,
        blocking=blocking_raw.lower() == 'true',
        timeout_ms=300000,
    )


def build_gate_specs(
    effective_profile: str,
    skip_defaults: bool,
    custom_gates: list[str],
    profiles_config: dict[str, Any] | None = None,
) -> list[GateSpec]:
    if profiles_config is None:
        profiles_config = load_json(
            SKILL_ROOT / 'assets' / 'verification-profiles.json'
        )
    gate_defs = profiles_config.get('gates', {})
    gates: list[GateSpec] = []

    if not skip_defaults:
        profile_gates = (
            profiles_config.get('profiles', {})
            .get(effective_profile, {})
            .get('gates', [])
        )
        for gate_entry in profile_gates:
            gate_id = gate_entry['id']
            gate_config = gate_defs.get(gate_id, {})
            if not gate_config:
                continue
            gates.append(
                GateSpec(
                    name=gate_id,
                    label=str(gate_config.get('label', gate_id)),
                    command=str(gate_config.get('command', '')),
                    blocking=bool(
                        gate_entry.get(
                            'blocking', gate_config.get('blocking', True)
                        )
                    ),
                    timeout_ms=int(gate_config.get('timeoutMs', 300000)),
                    script=str(gate_config.get('script'))
                    if gate_config.get('script')
                    else None,
                    allow_missing=bool(gate_config.get('allowMissing', False)),
                ),
            )

    gates.extend(parse_custom_gate(raw_gate) for raw_gate in custom_gates)

    return gates


def failure_classification(output: str, exit_code: int | None) -> str:
    lowered = output.lower()
    if 'missing script' in lowered or 'unknown script' in lowered:
        return 'not_configured'
    if exit_code == 127:
        return 'environment'
    environment_signals = [
        'command not found',
        'no such file or directory',
        'enoent',
        'permission denied',
        'timed out',
        "playwright executable doesn't exist",
        'please run the following command to download new browsers',
    ]
    if any(signal in lowered for signal in environment_signals):
        return 'environment'
    return 'code'


def relative_log_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def write_gate_log(
    session_dir: str | None, gate_name: str, output: str
) -> str | None:
    if not session_dir:
        return None
    logs_dir = REPO_ROOT / session_dir / 'logs' / 'ai-verify'
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f'{gate_name}.log'
    log_path.write_text(output, encoding='utf-8')
    return relative_log_path(log_path)


def run_gate(
    spec: GateSpec,
    package_scripts: dict[str, str],
    dry_run: bool,
    session_dir: str | None,
) -> dict[str, Any]:
    if dry_run:
        return {
            'name': spec.name,
            'label': spec.label,
            'command': spec.command,
            'blocking': spec.blocking,
            'status': 'skipped',
            'classification': 'not_applicable',
            'durationMs': 0,
            'exitCode': 0,
            'logPath': None,
            'details': 'Dry run; gate nao foi executado.',
        }

    if spec.script and spec.script not in package_scripts:
        status = 'skipped' if spec.allow_missing else 'external_failure'
        details = f'Script repo-native ausente: npm run {spec.script}'
        return {
            'name': spec.name,
            'label': spec.label,
            'command': spec.command,
            'blocking': spec.blocking,
            'status': status,
            'classification': 'not_configured',
            'durationMs': 0,
            'exitCode': None,
            'logPath': write_gate_log(session_dir, spec.name, details),
            'details': details,
        }

    started_at = time.perf_counter()
    output = ''
    exit_code: int | None = None
    status = 'passed'
    classification = 'code'

    try:
        result = subprocess.run(  # nosec B603
            shlex.split(spec.command),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=max(1, spec.timeout_ms // 1000),
            check=False,
        )
        exit_code = result.returncode
        output = (result.stdout or '') + (
            ('\n' + result.stderr) if result.stderr else ''
        )
        if exit_code == 0:
            status = 'passed'
            classification = 'code'
        else:
            classification = failure_classification(output, exit_code)
            if classification == 'code':
                status = 'failed'
            elif classification == 'not_configured' and spec.allow_missing:
                status = 'skipped'
            else:
                status = 'external_failure'
    except subprocess.TimeoutExpired as error:
        output = f'Command timed out after {spec.timeout_ms}ms.\n{error}'
        exit_code = 124
        status = 'external_failure'
        classification = 'environment'
    except OSError as error:
        output = str(error)
        exit_code = None
        status = 'external_failure'
        classification = 'environment'

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    output_lines = output.strip().splitlines()
    details_text = '\n'.join(output_lines[:10]).strip()
    return {
        'name': spec.name,
        'label': spec.label,
        'command': spec.command,
        'blocking': spec.blocking,
        'status': status,
        'classification': classification,
        'durationMs': duration_ms,
        'exitCode': exit_code,
        'logPath': write_gate_log(session_dir, spec.name, output),
        'details': details_text,
    }


def _new_precommit_hook(match: re.Match[str]) -> dict[str, Any]:
    label = match.group('label').strip()
    return {
        'hook_id': label.replace(' ', '-').lower(),
        'label': label,
        'status': match.group('status').lower(),
        'classification': 'code',
        'exit_code': None,
        'modified_files': False,
        'duration_ms': 0,
    }


def _consume_precommit_detail(
    current_hook: dict[str, Any],
    line: str,
) -> None:
    if line.startswith('- hook id: '):
        current_hook['hook_id'] = line.split('- hook id: ')[1].strip()
    elif line.startswith('- exit code: '):
        with contextlib.suppress(ValueError):
            current_hook['exit_code'] = int(
                line.split('- exit code: ')[1].strip()
            )
    elif 'files were modified by this hook' in line:
        current_hook['modified_files'] = True
        current_hook['classification'] = 'code'

    if current_hook.get('exit_code') == 127:
        current_hook['classification'] = 'environment'
    if 'Executable' in line and 'not found' in line:
        current_hook['classification'] = 'environment'


def _append_precommit_hook(
    results: list[dict[str, Any]],
    current_hook: dict[str, Any] | None,
    details_buffer: list[str],
) -> None:
    if current_hook is not None:
        current_hook['details'] = '\n'.join(details_buffer).strip()
        results.append(current_hook)


def _finalize_precommit_hook(
    hook: dict[str, Any],
) -> PrecommitHookResult:
    details_text = str(hook['details'])
    lines_detail = details_text.splitlines()
    if len(lines_detail) > 10:
        details_text = '\n'.join(lines_detail[:10])
    if hook['modified_files']:
        details_text = (
            'autofix aplicado — arquivos modificados, reexecute\n'
            + details_text
        )
    return PrecommitHookResult(
        hook_id=hook['hook_id'],
        label=hook['label'],
        status=hook['status'],
        classification=hook['classification'],
        exit_code=hook['exit_code'],
        details=details_text.strip(),
        modified_files=hook['modified_files'],
        duration_ms=hook['duration_ms'],
    )


def parse_precommit_output(output: str) -> list[PrecommitHookResult]:
    results: list[dict[str, Any]] = []
    current_hook: dict[str, Any] | None = None
    details_buffer: list[str] = []

    result_regex = re.compile(
        r'^(?P<label>.+?)\.+(?:\(no files to check\))?\s*(?P<status>Passed|Failed|Skipped)\s*$',
        re.IGNORECASE,
    )

    for line in output.splitlines():
        match = result_regex.match(line)
        if match:
            _append_precommit_hook(results, current_hook, details_buffer)
            current_hook = _new_precommit_hook(match)
            details_buffer = []
        elif current_hook and current_hook['status'] == 'failed':
            details_buffer.append(line)
            _consume_precommit_detail(current_hook, line)

    _append_precommit_hook(results, current_hook, details_buffer)
    return [_finalize_precommit_hook(hook) for hook in results]


def load_hook_policy() -> dict[str, Any]:
    policy_path = SKILL_ROOT / 'assets' / 'precommit-hook-policy.json'
    if not policy_path.exists():
        return {}
    hooks = load_json(policy_path).get('hooks', {})
    return hooks if isinstance(hooks, dict) else {}


def list_hooks_from_config_as_dry_run() -> list[dict[str, Any]]:
    config_path = REPO_ROOT / '.pre-commit-config.yaml'
    if not config_path.exists():
        return [
            {
                'name': 'pre-commit-config',
                'label': 'Missing config',
                'command': 'pre-commit run',
                'blocking': True,
                'status': 'external_failure',
                'classification': 'not_configured',
                'durationMs': 0,
                'exitCode': 1,
                'logPath': None,
                'details': '.pre-commit-config.yaml not found',
            }
        ]

    try:
        import yaml
    except ImportError:
        return [
            {
                'name': 'pre-commit',
                'label': 'Dry run fallback',
                'command': 'pre-commit run',
                'blocking': True,
                'status': 'skipped',
                'classification': 'not_applicable',
                'durationMs': 0,
                'exitCode': 0,
                'logPath': None,
                'details': 'pyyaml not found. Would run pre-commit run --all-files.',
            }
        ]

    config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    hooks = []
    policy = load_hook_policy()
    default_stages = config.get('default_stages', ['pre-commit'])
    if not isinstance(default_stages, list):
        default_stages = ['pre-commit']
    for repo in config.get('repos', []):
        for hook in repo.get('hooks', []):
            hook_id = hook['id']
            stages = hook.get('stages', default_stages)
            if not isinstance(stages, list):
                stages = default_stages
            for stage in VERIFY_HOOK_STAGES:
                if stage not in stages:
                    continue
                gate_name = f'{stage}:{hook_id}'
                hooks.append(
                    {
                        'name': gate_name,
                        'label': f'{hook.get("name", hook_id)} [{stage}]',
                        'command': (
                            f'pre-commit run {hook_id} --hook-stage {stage}'
                        ),
                        'blocking': policy.get(hook_id, {}).get(
                            'blocking', True
                        ),
                        'status': 'skipped',
                        'classification': 'not_applicable',
                        'durationMs': 0,
                        'exitCode': 0,
                        'logPath': None,
                        'details': 'Dry run; gate nao foi executado.',
                    }
                )
    return hooks


def resolve_scope(profile: str, changed_files: list[str]) -> list[str]:
    if profile in (
        'high-risk',
        'security-touch',
        'ui-flow',
    ) or PROFILE_PRIORITY.get(profile, 0) >= PROFILE_PRIORITY.get(
        'high-risk', 3
    ):
        return ['--all-files']
    if changed_files:
        return ['--files', *changed_files[:100]]
    return ['--all-files']


def to_gate(
    h: PrecommitHookResult,
    policy: dict[str, Any],
    session_dir: str | None,
    stage: str,
) -> dict[str, Any]:
    blocking = policy.get(h.hook_id, {}).get('blocking', True)
    gate_name = f'{stage}:{h.hook_id}'
    return {
        'name': gate_name,
        'label': f'{h.label} [{stage}]',
        'command': f'pre-commit run {h.hook_id} --hook-stage {stage}',
        'blocking': blocking,
        'status': h.status,
        'classification': h.classification,
        'durationMs': h.duration_ms,
        'exitCode': h.exit_code,
        'logPath': write_gate_log(session_dir, gate_name, h.details)
        if h.details
        else None,
        'details': h.details or 'Passed/Skipped without output',
    }


def _run_precommit_stage(
    stage: str,
    scope: list[str],
    session_dir: str | None,
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    cmd = ['pre-commit', 'run', '--hook-stage', stage, *scope]
    started = time.perf_counter()
    try:
        result = subprocess.run(  # nosec B603
            cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=600
        )
    except FileNotFoundError:
        return [
            {
                'name': f'{stage}:pre-commit',
                'label': f'pre-commit setup [{stage}]',
                'command': ' '.join(cmd),
                'blocking': True,
                'status': 'external_failure',
                'classification': 'not_configured',
                'durationMs': 0,
                'exitCode': 127,
                'logPath': None,
                'details': 'pre-commit command not found. Please install pre-commit first.',
            }
        ]
    except subprocess.TimeoutExpired as error:
        return [
            {
                'name': f'{stage}:pre-commit-timeout',
                'label': f'pre-commit timeout [{stage}]',
                'command': ' '.join(cmd),
                'blocking': True,
                'status': 'external_failure',
                'classification': 'environment',
                'durationMs': 600000,
                'exitCode': 124,
                'logPath': None,
                'details': f'Command timed out after 600s.\n{error}',
            }
        ]

    duration_ms = int((time.perf_counter() - started) * 1000)
    output = result.stdout + result.stderr
    hook_results = parse_precommit_output(output)

    if not hook_results:
        classification = (
            failure_classification(output, result.returncode)
            if result.returncode != 0
            else 'code'
        )
        status = (
            'passed'
            if result.returncode == 0
            else (
                'external_failure'
                if classification in {'environment', 'not_configured'}
                else 'failed'
            )
        )
        gate_name = f'{stage}:pre-commit-raw'
        return [
            {
                'name': gate_name,
                'label': f'pre-commit (fallback) [{stage}]',
                'command': ' '.join(cmd),
                'blocking': True,
                'status': status,
                'classification': classification,
                'durationMs': duration_ms,
                'exitCode': result.returncode,
                'logPath': write_gate_log(session_dir, gate_name, output),
                'details': output.strip()
                or 'No output and no hooks detected.',
            }
        ]

    return [to_gate(h, policy, session_dir, stage) for h in hook_results]


def run_precommit_mode(
    changed_files: list[str],
    effective_profile: str,
    dry_run: bool,
    session_dir: str | None,
) -> list[dict[str, Any]]:
    if dry_run:
        return list_hooks_from_config_as_dry_run()

    scope = resolve_scope(effective_profile, changed_files)
    policy = load_hook_policy()
    results: list[dict[str, Any]] = []
    for stage in VERIFY_HOOK_STAGES:
        results.extend(
            _run_precommit_stage(
                stage=stage,
                scope=scope,
                session_dir=session_dir,
                policy=policy,
            )
        )
    return results


def summarize_gates(
    gates: list[dict[str, Any]], dry_run: bool, effective_profile: str
) -> str:
    if dry_run:
        return f'Dry run: {len(gates)} gates selecionados para o perfil {effective_profile}.'
    counts = dict.fromkeys(GATE_STATUSES, 0)
    for gate in gates:
        counts[gate['status']] += 1
    parts = []
    for status in ('passed', 'failed', 'external_failure', 'skipped'):
        amount = counts[status]
        if amount:
            parts.append(f'{amount} {status}')
    return ', '.join(parts) if parts else 'Nenhum gate executado.'


def overall_status(gates: list[dict[str, Any]], dry_run: bool) -> str:
    if dry_run:
        return 'skipped'
    blocking_gates = [gate for gate in gates if gate['blocking']]
    if not gates or all(gate['status'] == 'skipped' for gate in gates):
        return 'skipped'
    if any(gate['status'] == 'failed' for gate in blocking_gates):
        return 'failed'
    if any(gate['status'] == 'external_failure' for gate in blocking_gates):
        return 'external_failure'
    return 'passed'


def should_fail_exit_code(gates: list[dict[str, Any]]) -> bool:
    return any(
        gate['blocking'] and gate['status'] in {'failed', 'external_failure'}
        for gate in gates
    )


def load_runtime_support():
    sys.path.append(str(REPO_ROOT / '.agents' / 'runtime' / 'review'))
    from runtime_support import (
        assert_transition,
        build_empty_gate_report,
        ensure_session_layout,
        load_or_migrate_artifact,
        now_iso,
        resolve_session_dir,
        save_artifact,
    )

    return {
        'assert_transition': assert_transition,
        'build_empty_gate_report': build_empty_gate_report,
        'ensure_session_layout': ensure_session_layout,
        'load_or_migrate_artifact': load_or_migrate_artifact,
        'now_iso': now_iso,
        'resolve_session_dir': resolve_session_dir,
        'save_artifact': save_artifact,
    }


def persist_gate_report(result: dict[str, Any]) -> None:
    session_dir = result['sessionDir']
    if not session_dir:
        return

    runtime = load_runtime_support()
    resolved_session_dir = runtime['resolve_session_dir'](
        session_dir=session_dir
    )
    runtime['ensure_session_layout'](resolved_session_dir)

    session_artifact_path = (
        resolved_session_dir / 'artifacts' / 'review-session.json'
    )
    review_id = resolved_session_dir.name
    if session_artifact_path.exists():
        session_artifact = runtime['load_or_migrate_artifact'](
            resolved_session_dir, 'review-session'
        )
        review_id = session_artifact['reviewId']

    gate_report_path = resolved_session_dir / 'artifacts' / 'gate-report.json'
    if gate_report_path.exists():
        gate_report = runtime['load_or_migrate_artifact'](
            resolved_session_dir, 'gate-report'
        )
    else:
        gate_report = runtime['build_empty_gate_report'](review_id)

    if gate_report['status'] == 'pending':
        runtime['assert_transition']('gate-report', 'pending', 'completed')

    gate_report.update(
        {
            'artifactType': 'gate-report',
            'reviewId': review_id,
            'status': 'completed',
            'updatedAt': runtime['now_iso'](),
            'profile': result['profile'],
            'effectiveProfile': result['effectiveProfile'],
            'profileReason': result['profileReason'],
            'changedFiles': result['changedFiles'],
            'escalations': result['escalations'],
            'summary': result['summary'],
            'gates': [
                {
                    'gateId': gate['name'],
                    'label': gate['label'],
                    'command': gate['command'],
                    'blocking': gate['blocking'],
                    'status': gate['status'],
                    'classification': gate['classification'],
                    'startedAt': gate_report.get(
                        'updatedAt', runtime['now_iso']()
                    ),
                    'finishedAt': runtime['now_iso'](),
                    'durationSeconds': round(gate['durationMs'] / 1000, 3),
                    'durationMs': gate['durationMs'],
                    'exitCode': gate['exitCode']
                    if isinstance(gate['exitCode'], int)
                    else 0,
                    'outcome': gate.get('details', ''),
                    'logPath': gate['logPath'],
                }
                for gate in result['gates']
            ],
        },
    )
    runtime['save_artifact'](resolved_session_dir, gate_report)


def validate_result_shape(result: dict[str, Any]) -> None:
    if result['status'] not in TOP_LEVEL_STATUSES:
        raise ValueError(f'invalid status {result["status"]!r}')
    for gate in result['gates']:
        if gate['status'] not in GATE_STATUSES:
            raise ValueError(f'invalid gate status {gate["status"]!r}')
        if gate['classification'] not in CLASSIFICATIONS:
            raise ValueError(
                f'invalid gate classification {gate["classification"]!r}'
            )


def main() -> int:
    args = parse_args()
    config = load_verification_config()
    valid_profiles = {'auto', *config['profiles']}
    if args.profile not in valid_profiles:
        choices = ', '.join(sorted(valid_profiles))
        raise SystemExit(
            f'ai-verify.py: error: argument --profile: invalid choice: '
            f'{args.profile!r} (choose from {choices})'
        )
    path_rules = config['pathRules']
    escalation_rules = config['escalationRules']
    package_scripts = load_package_scripts()
    changed_files = detect_changed_files(args.changed_file, args.session_dir)
    effective_profile, profile_reason = resolve_effective_profile(
        args.profile,
        changed_files,
        path_rules,
    )
    profile_config = config['profiles'].get(effective_profile, {})
    profile_has_gates = bool(profile_config.get('gates'))
    if args.mode == 'precommit' and not profile_has_gates:
        gate_results = run_precommit_mode(
            changed_files, effective_profile, args.dry_run, args.session_dir
        )
    else:
        gates = build_gate_specs(
            effective_profile=effective_profile,
            skip_defaults=args.skip_defaults,
            custom_gates=args.gate,
            profiles_config=config,
        )
        gate_results = [
            run_gate(
                spec=gate,
                package_scripts=package_scripts,
                dry_run=args.dry_run,
                session_dir=args.session_dir,
            )
            for gate in gates
        ]
    result = {
        'schemaVersion': AI_VERIFY_SCHEMA_VERSION,
        'status': overall_status(gate_results, args.dry_run),
        'profile': args.profile,
        'effectiveProfile': effective_profile,
        'profileReason': profile_reason,
        'changedFiles': changed_files,
        'gates': gate_results,
        'escalations': collect_escalation_reasons(
            changed_files=changed_files,
            effective_profile=effective_profile,
            escalation_rules=escalation_rules,
        ),
        'sessionDir': args.session_dir,
        'summary': summarize_gates(
            gate_results, args.dry_run, effective_profile
        ),
    }

    if (
        any(
            gate['status'] in {'failed', 'external_failure'}
            for gate in gate_results
        )
        and not result['escalations']['reviewRequired']
    ):
        result['escalations']['reviewRequired'] = True
        result['escalations']['reasons'].append(
            'Falha de gate exige revisao ou remediacao antes do encerramento.',
        )

    result['escalations']['reasons'] = list(
        dict.fromkeys(result['escalations']['reasons'])
    )
    validate_result_shape(result)
    if args.session_dir and not args.dry_run:
        persist_gate_report(result)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 1 if should_fail_exit_code(gate_results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
