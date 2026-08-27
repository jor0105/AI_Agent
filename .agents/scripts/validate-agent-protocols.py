#!/usr/bin/env python3
"""Validate review-flow agents and protocol skills."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.consumer_validators import parse_frontmatter
from harness.selection import (
    SelectionError,
    load_review_owner,
    review_owner_name,
)

HARNESS_ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = HARNESS_ROOT / 'agents'
WORKFLOWS_DIR = HARNESS_ROOT / 'workflows'
SKILLS_ROOT = HARNESS_ROOT / 'skills'
LINT_AND_VALIDATE_SKILL_DIR = SKILLS_ROOT / 'lint-and-validate'
REVIEW_OWNER_PATH = HARNESS_ROOT / 'harness' / 'review-owner.json'
REVIEW_RUNTIME_ROOT = HARNESS_ROOT / 'runtime' / 'review'
PACK_REGISTRY_PATH = REVIEW_RUNTIME_ROOT / 'pack-registry.json'


EXPECTED_AGENTS = {
    'developer-engineer',
    'security-engineer',
}

REQUIRED_AGENT_SECTIONS = [
    'Identity',
    'Can Do',
    'Cannot Do',
    'Done When',
]

LEGACY_AGENT_SECTIONS = [
    'Skill Routing',
    'Escalation',
    'Activation Rule',
    'Required Inputs',
    'Preflight',
    'Context Policy',
    'Phase Machine',
    'Failure Branches',
    'Success Exit',
    'Stop Conditions',
    'Hard Boundaries',
]

REQUIRED_SKILL_SECTIONS = [
    'Contexto',
    'Procedimento',
    'Scripts',
    'Se Algo Falhar',
    'Condições de Saída',
    'Saída Esperada',
    'Exemplos',
    'Evals de trigger',
    'Evals de workflow',
]

SKILL_PATH_RE = re.compile(r'\.agents/skills/[A-Za-z0-9._\-/]+/SKILL\.md')
SCRIPT_PATH_RE = re.compile(r'\.agents/skills/[A-Za-z0-9._\-/]+\.(?:py|sh)')
SESSION_PATH_RE = re.compile(r'\.agents/sessions/[A-Za-z0-9._<>\-/]+')
HEADING_RE = re.compile(r'^##\s+(.+?)\s*$', re.MULTILINE)
REQUIRED_AGENT_SKILL_METADATA = ['name', 'description']
ALLOWED_AGENT_SKILL_METADATA = {'name', 'description'}
VALIDATION_SCOPE = 'agents-review-protocol'

REVIEW_OWNER_ASSET_LAYOUT = {
    'review-session': (
        ('templates', 'review-session.template.md'),
        ('schemas', 'review-session.schema.json'),
    ),
    'review-plan': (
        ('templates', 'review-plan.template.md'),
        ('schemas', 'review-plan.schema.json'),
    ),
    'finding': (
        ('templates', 'finding.template.md'),
        ('schemas', 'finding.schema.json'),
    ),
    'security-handoff': (
        ('templates', 'security-handoff.template.md'),
        ('schemas', 'security-handoff.schema.json'),
    ),
    'verdict': (
        ('templates', 'verdict.template.md'),
        ('schemas', 'verdict.schema.json'),
    ),
    'review-summary': (('templates', 'review-summary.template.md'),),
}

# The verification runner itself is owned by each consuming project: it
# encodes that repository's gates, paths and escalations. The harness ships
# the contract it must satisfy — schema and profiles — not the runner.
EXPECTED_VERIFY_ASSETS = [
    LINT_AND_VALIDATE_SKILL_DIR / 'schemas' / 'ai-verify.schema.json',
    LINT_AND_VALIDATE_SKILL_DIR / 'assets' / 'verification-profiles.json',
    LINT_AND_VALIDATE_SKILL_DIR / 'assets' / 'path-rules.json',
    LINT_AND_VALIDATE_SKILL_DIR / 'assets' / 'escalation-rules.json',
]


PROHIBITED_GLOBAL_RULE_PATTERNS = [
    re.compile(r'Double quotes', re.IGNORECASE),
    re.compile(r'Semicolons', re.IGNORECASE),
    re.compile(r'2-space indentation', re.IGNORECASE),
    re.compile(r'Import order', re.IGNORECASE),
    re.compile(r'Use @/ imports', re.IGNORECASE),
    re.compile(r'UI copy is pt-BR', re.IGNORECASE),
    re.compile(r'\bKISS\b', re.IGNORECASE),
    re.compile(r'\bYAGNI\b', re.IGNORECASE),
    re.compile(r'Clean Code', re.IGNORECASE),
    re.compile(r'\bSOLID\b', re.IGNORECASE),
]

PROHIBITED_PROTOCOL_SKILL_PHRASES = [
    'The owning agent needs this focused internal workflow.',
    'A direct implementation, review, or validation step is enough.',
    'The request belongs to a different owner or broader coordination flow.',
]

AUTOMATED_MODEL_ACTION_RE = re.compile(
    r'\b(?:select|recommend|infer|rank|switch|choose|pick|classif(?:y|ies)|'
    r'request|solicit)\w*\b.{0,80}\bmodel(?:\s+metadata)?\b',
    re.IGNORECASE,
)
MODEL_PROVIDER_NAME_RE = re.compile(
    r'\b(?:gpt-\d[\w.-]*|claude-(?:\d[\w.-]*)|'
    r'(?:claude|gemini)\s+(?:sonnet|opus|haiku|pro|flash)|'
    r'o[134](?:-[\w.-]+)?|llama-\d[\w.-]*)\b',
    re.IGNORECASE,
)
MODEL_POLICY_NEGATION_MARKERS = (
    'do not',
    'does not',
    'must not',
    'never',
    'no model',
    'manual',
    'user-selected',
    'user selected',
    'not select',
    'not recommend',
    'not infer',
    'not rank',
    'not switch',
    'not request',
    'não',
    'nao',
    'sem modelo',
)

DANGLING_REVIEW_REFERENCES = [
    '.agents/runtime/' + 'reviewer',
    'runtime/' + 'reviewer',
    'reviewer.agent.md',
    'reviewer.manifest.json',
    '.agents/skills/' + 'review-closeout',
    '.agents/skills/' + 'review-item',
    '.agents/skills/' + 'review-session',
]

DANGLING_REF_IGNORED_DIR_PARTS = {
    '.git',
    'fixtures',
    '__pycache__',
    'sessions',
}


def extract_frontmatter(text: str) -> str:
    if not text.startswith('---\n'):
        return ''
    parts = text.split('---\n', 2)
    if len(parts) < 3:
        return ''
    return parts[1]


def parse_metadata_value(raw_value: str) -> object:
    raw_value = raw_value.strip().strip('"\'')
    if raw_value.startswith('[') and raw_value.endswith(']'):
        inner = raw_value[1:-1].strip()
        if not inner:
            return []
        return [
            item.strip().strip('"\'')
            for item in inner.split(',')
            if item.strip()
        ]
    return raw_value


def _parse_frontmatter_metadata(frontmatter: str) -> dict[str, object]:
    if not frontmatter.strip():
        return {}
    try:
        meta, _ = parse_frontmatter(f'---\n{frontmatter}\n---\n')
        return meta
    except ValueError:
        return {}


def _parse_frontmatter_agents(frontmatter: str) -> list[str]:
    match = re.search(r'agents:\s*\[(.*?)\]', frontmatter, re.DOTALL)
    if not match:
        return []
    return [
        c.strip().strip('"\'')
        for c in match.group(1).replace('\n', ' ').split(',')
        if c.strip()
    ]


def _parse_frontmatter_fields(
    text: str,
) -> tuple[dict[str, object], list[str]]:
    frontmatter = extract_frontmatter(text)
    return (
        _parse_frontmatter_metadata(frontmatter),
        _parse_frontmatter_agents(frontmatter),
    )


def parse_frontmatter_metadata(text: str) -> dict[str, object]:
    metadata, _ = _parse_frontmatter_fields(text)
    return metadata


def parse_frontmatter_agents(text: str) -> list[str]:
    _, agents = _parse_frontmatter_fields(text)
    return agents


def normalize_heading(heading: str) -> str:
    return heading.split(' — ', 1)[0].strip()


def _normalized_headings(text: str) -> set[str]:
    return {normalize_heading(heading) for heading in HEADING_RE.findall(text)}


def missing_sections(text: str, required: list[str]) -> list[str]:
    headings = _normalized_headings(text)
    return [section for section in required if section not in headings]


def find_present_sections(text: str, candidates: list[str]) -> list[str]:
    headings = _normalized_headings(text)
    return [section for section in candidates if section in headings]


def validate_session_reference(ref: str) -> bool:
    if ref == '.agents/sessions/<review-id>':
        return True
    if ref == '.agents/sessions/.../artifacts':
        return True
    if ref == '.agents/sessions/.../views':
        return True
    if ref.startswith('.agents/sessions/review-'):
        return True
    if '/artifacts/' in ref:
        return ref.endswith(('.json', '/'))
    if '/views/' in ref:
        return ref.endswith(('.md', '/'))
    return False


def collect_paths(text: str, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(text))


def _validate_reference_paths(
    source_file: Path,
    text: str,
    errors: list[str],
    *,
    skill_error: str,
    script_error: str,
    include_sessions: bool,
) -> None:
    errors.extend(
        f'{source_file}: {skill_error} {skill_path}'
        for skill_path in collect_paths(text, SKILL_PATH_RE)
        if not (HARNESS_ROOT / skill_path).exists()
    )
    errors.extend(
        f'{source_file}: {script_error} {script_path}'
        for script_path in collect_paths(text, SCRIPT_PATH_RE)
        if not (HARNESS_ROOT / script_path).exists()
    )
    if include_sessions:
        errors.extend(
            f'{source_file}: invalid session reference {session_ref}'
            for session_ref in collect_paths(text, SESSION_PATH_RE)
            if not validate_session_reference(session_ref)
        )


def load_json(path: Path, errors: list[str]) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        errors.append(f'missing json file: {path}')
        return None
    except json.JSONDecodeError as exc:
        errors.append(f'{path}: invalid json ({exc})')
        return None

    if not isinstance(payload, dict):
        errors.append(f'{path}: root payload must be an object')
        return None
    return payload


def extract_section_body(text: str, heading: str) -> str | None:
    pattern = re.compile(rf'^##\s+{re.escape(heading)}\s*$', re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        return None

    start = match.end()
    next_heading = re.search(r'^##\s+.+\s*$', text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def validate_prompt_shape(
    agent_file: Path, text: str, errors: list[str]
) -> None:
    missing = missing_sections(text, REQUIRED_AGENT_SECTIONS)
    if missing:
        errors.append(f'{agent_file}: missing agent sections {missing}')

    legacy_sections = find_present_sections(text, LEGACY_AGENT_SECTIONS)
    if legacy_sections:
        errors.append(
            f'{agent_file}: legacy agent sections still present {legacy_sections}'
        )

    errors.extend(
        f"{agent_file}: duplicates global rule phrase '{phrase.pattern}' that belongs in AGENTS.md"
        for phrase in PROHIBITED_GLOBAL_RULE_PATTERNS
        if phrase.search(text)
    )


def validate_agent_skill_metadata(
    skill_file: Path, text: str, errors: list[str]
) -> None:
    metadata = parse_frontmatter_metadata(text)
    missing = [
        key for key in REQUIRED_AGENT_SKILL_METADATA if key not in metadata
    ]
    if missing:
        errors.append(
            f'{skill_file}: missing agent-only skill metadata {missing}'
        )
        return

    expected_name = skill_file.parent.name
    if metadata.get('name') != expected_name:
        errors.append(
            f"{skill_file}: metadata name should be '{expected_name}', got '{metadata.get('name')}'"
        )

    extras = sorted(set(metadata) - ALLOWED_AGENT_SKILL_METADATA)
    if extras:
        errors.append(
            f'{skill_file}: frontmatter de skill deve seguir o contrato mínimo de skill-governance; remova {extras}'
        )

    lowered = text.lower()
    errors.extend(
        f"{skill_file}: contains generic placeholder phrase '{phrase}'"
        for phrase in PROHIBITED_PROTOCOL_SKILL_PHRASES
        if phrase.lower() in lowered
    )


def _is_manual_model_policy_line(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in MODEL_POLICY_NEGATION_MARKERS)


def validate_no_automated_model_selection(errors: list[str]) -> None:
    """Reject model automation only in agent and OpenSpec contracts."""
    contract_files = [
        *sorted(AGENT_DIR.glob('*.agent.md')),
        *sorted(WORKFLOWS_DIR.glob('opsx-*.prompt.md')),
    ]
    for path in contract_files:
        for line_number, line in enumerate(
            path.read_text(encoding='utf-8').splitlines(), start=1
        ):
            if _is_manual_model_policy_line(line):
                continue
            if AUTOMATED_MODEL_ACTION_RE.search(line):
                errors.append(
                    f'{path}:{line_number}: forbidden automated model-selection policy'
                )
            elif MODEL_PROVIDER_NAME_RE.search(line):
                errors.append(
                    f'{path}:{line_number}: forbidden provider model name in agent/workflow contract'
                )


def _load_review_owner(errors: list[str]) -> tuple[str | None, bool]:
    try:
        return load_review_owner(REVIEW_OWNER_PATH), True
    except SelectionError as exc:
        errors.append(str(exc))
        return None, False


def _review_owner_root(review_owner: str) -> Path:
    return SKILLS_ROOT / review_owner_name(review_owner)


def expected_artifact_assets(
    review_owner: str | None,
) -> dict[str, list[Path]]:
    assets = {
        'gate-report': [
            LINT_AND_VALIDATE_SKILL_DIR
            / 'templates'
            / 'gate-report.template.md',
            LINT_AND_VALIDATE_SKILL_DIR
            / 'schemas'
            / 'gate-report.schema.json',
        ]
    }
    if review_owner is None:
        return assets

    owner_root = _review_owner_root(review_owner)
    assets.update(
        {
            artifact_type: [owner_root.joinpath(*parts) for parts in layout]
            for artifact_type, layout in REVIEW_OWNER_ASSET_LAYOUT.items()
        }
    )
    return assets


def expected_review_runtime_assets(review_owner: str | None) -> list[Path]:
    assets = [REVIEW_RUNTIME_ROOT / 'runtime_support.py']
    if review_owner is not None:
        assets.extend(
            [
                PACK_REGISTRY_PATH,
                REVIEW_RUNTIME_ROOT / 'review-rubric.md',
            ]
        )
    return assets


def _stale_review_owner_assets() -> list[Path]:
    assets: list[Path] = []
    for layout in REVIEW_OWNER_ASSET_LAYOUT.values():
        for directory, filename in layout:
            assets.extend(SKILLS_ROOT.glob(f'*/{directory}/{filename}'))
    return sorted(set(assets))


def validate_artifact_asset_layout(
    review_owner: str | None, errors: list[str]
) -> None:
    for artifact_type, asset_paths in expected_artifact_assets(
        review_owner
    ).items():
        errors.extend(
            f'missing {artifact_type} artifact asset: {asset_path}'
            for asset_path in asset_paths
            if not asset_path.exists()
        )

    for legacy_dir_name in ('templates', 'schemas'):
        legacy_dir = HARNESS_ROOT / legacy_dir_name
        if legacy_dir.exists() and any(legacy_dir.iterdir()):
            errors.append(
                f'legacy .agents/{legacy_dir_name} must stay empty or absent'
            )

    errors.extend(
        f'missing ai:verify asset: {asset_path}'
        for asset_path in EXPECTED_VERIFY_ASSETS
        if not asset_path.exists()
    )
    errors.extend(
        f'missing review runtime asset: {asset_path}'
        for asset_path in expected_review_runtime_assets(review_owner)
        if not asset_path.exists()
    )
    if review_owner is None:
        errors.extend(
            f'retired review unit retains owner asset: {asset_path}'
            for asset_path in _stale_review_owner_assets()
        )
        if PACK_REGISTRY_PATH.exists():
            errors.append(
                f'retired review unit retains pack registry: '
                f'{PACK_REGISTRY_PATH}'
            )


def validate_no_dangling_review_runtime_refs(errors: list[str]) -> None:
    search_roots = [HARNESS_ROOT, HARNESS_ROOT / 'docs']
    ignored_files = {
        'validate-agent-protocols.py',
    }

    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob('*'):
            if not path.is_file() or path.name in ignored_files:
                continue
            if any(
                part in DANGLING_REF_IGNORED_DIR_PARTS for part in path.parts
            ):
                continue
            if path.suffix not in {'.md', '.json', '.py', '.toml', '.yml'}:
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            errors.extend(
                f'{path}: dangling legacy review reference {reference}'
                for reference in DANGLING_REVIEW_REFERENCES
                if reference in text
            )


def _run_protocol_script(
    review_owner: str,
    script_name: str,
    *args: str,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    script_path = _review_owner_root(review_owner) / 'scripts' / script_name
    return subprocess.run(
        [sys.executable, str(script_path), *args],
        cwd=HARNESS_ROOT,
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
    )


def validate_review_owner_smoke(
    review_owner: str | None, errors: list[str]
) -> None:
    if review_owner is None:
        return
    owner_name = review_owner_name(review_owner)
    with tempfile.TemporaryDirectory(prefix='review-protocol-') as tmp:
        session_dir = Path(tmp) / 'session'
        commands = [
            (
                'init-review-session.py',
                [
                    '--session-dir',
                    str(session_dir),
                    '--change-type',
                    'bug-fix',
                    '--changed-by',
                    owner_name,
                    '--security-touch',
                    'no',
                    '--changed-file',
                    'src/main.py',
                ],
                None,
            ),
            (
                'build-review-plan.py',
                ['--session-dir', str(session_dir)],
                None,
            ),
        ]

        for script_name, args, input_text in commands:
            result = _run_protocol_script(
                review_owner, script_name, *args, input_text=input_text
            )
            if result.returncode != 0:
                errors.append(
                    f'{script_name}: smoke failed: {result.stderr.strip()}'
                )
                return

        plan_path = session_dir / 'artifacts' / 'review-plan.json'
        try:
            plan = json.loads(plan_path.read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            errors.append(f'{plan_path}: smoke cannot read plan ({exc})')
            return

        items = plan.get('items')
        if not isinstance(items, list) or not items:
            errors.append(f'{plan_path}: smoke did not create review items')
            return

        for item in items:
            item_id = item.get('itemId') if isinstance(item, dict) else None
            if not isinstance(item_id, str):
                errors.append(f'{plan_path}: smoke item is missing itemId')
                return
            result = _run_protocol_script(
                review_owner,
                'mark-review-item-done.py',
                '--session-dir',
                str(session_dir),
                '--item-id',
                item_id,
            )
            if result.returncode != 0:
                errors.append(
                    'mark-review-item-done.py: smoke failed: '
                    f'{result.stderr.strip()}'
                )
                return

        for script_name in (
            'consolidate-verdict.py',
            'export-review-summary.py',
        ):
            result = _run_protocol_script(
                review_owner, script_name, '--session-dir', str(session_dir)
            )
            if result.returncode != 0:
                errors.append(
                    f'{script_name}: smoke failed: {result.stderr.strip()}'
                )
                return


def main() -> int:
    agent_files = sorted(AGENT_DIR.glob('*.agent.md'))
    errors: list[str] = []
    review_owner, owner_is_valid = _load_review_owner(errors)
    skill_files = (
        [_review_owner_root(review_owner) / 'SKILL.md']
        if owner_is_valid and review_owner is not None
        else []
    )

    found_agents = {path.name.replace('.agent.md', '') for path in agent_files}
    if found_agents != EXPECTED_AGENTS:
        errors.append(
            'agent set mismatch: '
            f'expected={sorted(EXPECTED_AGENTS)} found={sorted(found_agents)}'
        )

    for agent_file in agent_files:
        text = agent_file.read_text(encoding='utf-8')
        validate_prompt_shape(agent_file, text, errors)

        metadata, subagents = _parse_frontmatter_fields(text)
        if metadata.get('name') != agent_file.stem.replace('.agent', ''):
            errors.append(
                f'{agent_file}: frontmatter name must match filename'
            )

        errors.extend(
            f'{agent_file}: missing referenced subagent {subagent}'
            for subagent in subagents
            if not (AGENT_DIR / f'{subagent}.agent.md').exists()
        )
        _validate_reference_paths(
            agent_file,
            text,
            errors,
            skill_error='missing skill path',
            script_error='missing script path',
            include_sessions=True,
        )

    for skill_file in skill_files:
        if not skill_file.exists():
            errors.append(f'missing protocol skill: {skill_file}')
            continue

        text = skill_file.read_text(encoding='utf-8')
        validate_agent_skill_metadata(skill_file, text, errors)
        missing = missing_sections(text, REQUIRED_SKILL_SECTIONS)
        if missing:
            errors.append(f'{skill_file}: missing skill sections {missing}')

        _validate_reference_paths(
            skill_file,
            text,
            errors,
            skill_error='missing nested skill path',
            script_error='missing script path',
            include_sessions=False,
        )

    if owner_is_valid:
        validate_artifact_asset_layout(review_owner, errors)
    validate_no_dangling_review_runtime_refs(errors)
    validate_no_automated_model_selection(errors)
    if owner_is_valid:
        validate_review_owner_smoke(review_owner, errors)

    result = {
        'scope': VALIDATION_SCOPE,
        'status': 'ok' if not errors else 'error',
        'agents_checked': len(agent_files),
        'protocol_skills_checked': len(skill_files),
        'skills_checked': len(skill_files),
        'expected_agent_sections': REQUIRED_AGENT_SECTIONS,
        'expected_skill_sections': REQUIRED_SKILL_SECTIONS,
        'errors': errors,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
