"""Allowlisted generic static validators for consumer validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCOPE_VALIDATORS: dict[str, list[str]] = {
    'skills': ['skill.frontmatter', 'skill.references', 'skill.structure'],
    'agents': ['agent.frontmatter', 'agent.references', 'agent.structure'],
    'workflows': [
        'workflow.frontmatter',
        'workflow.references',
        'workflow.structure',
    ],
}

ALLOWED_SKILL_ACTIVE_FM = {'name', 'description'}
ALLOWED_SKILL_ARCHIVED_FM = {'name', 'description', 'status', 'replaced_by'}
ALLOWED_AGENT_FM = {'name', 'description', 'mode', 'agents'}
ALLOWED_WORKFLOW_FM = {'name', 'description', 'category', 'tags'}

AGENT_REQUIRED_SECTIONS = ('Identity', 'Can Do', 'Cannot Do', 'Done When')
AGENT_LEGACY_SECTIONS = (
    'Skill Routing', 'Escalation', 'Activation Rule', 'Required Inputs',
    'Preflight', 'Context Policy', 'Phase Machine', 'Failure Branches',
    'Success Exit', 'Stop Conditions', 'Hard Boundaries',
)


@dataclass(frozen=True)
class Diagnostic:
    item: str
    validator_id: str
    code: str
    message: str
    severity: str = 'error'

    def to_dict(self) -> dict[str, str]:
        return {
            'code': self.code,
            'item': self.item,
            'message': self.message,
            'severity': self.severity,
            'validatorId': self.validator_id,
        }


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse UTF-8 YAML frontmatter block and return (metadata, body)."""
    match = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n', text, re.DOTALL)
    if not match:
        raise ValueError(
            'frontmatter missing or malformed (expected --- ... ---)'
        )
    body = text[match.end() :]
    meta: dict[str, Any] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_key is not None:
            meta[current_key] = ' '.join(current_lines).strip()

    for line in match.group(1).splitlines():
        if line.startswith((' ', '\t')) and current_key:
            current_lines.append(line.strip())
            continue
        flush()
        current_key, current_lines = None, []
        if not line.strip() or ':' not in line:
            continue
        key, _, raw_val = line.partition(':')
        key, val = key.strip(), raw_val.strip().strip('"\'')
        if val in ('>', '>-', '|', '|-', '>+', '|+'):
            current_key = key
        elif val.startswith('[') and val.endswith(']'):
            inner = val[1:-1].strip()
            meta[key] = (
                [i.strip().strip('"\'') for i in inner.split(',') if i.strip()]
                if inner
                else []
            )
        else:
            meta[key] = val
    flush()
    return meta, body


def _check_declared_refs(
    root: Path, file_path: Path, text: str, v_id: str, code_prefix: str
) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    item_str = file_path.relative_to(root).as_posix()
    pattern = r'(?<![A-Za-z0-9._\-/])(?:references|assets|scripts|templates|schemas|data)/[A-Za-z0-9._\-/]+(?:\.[A-Za-z0-9._-]+)?'
    for ref in sorted(set(re.findall(pattern, text))):
        local_target = file_path.parent / ref
        root_target = root / ref
        target = local_target if local_target.exists() else (root_target if root_target.exists() else local_target)
        try:
            if not target.resolve().is_relative_to(root.resolve()):
                diags.append(
                    Diagnostic(
                        item_str,
                        v_id,
                        f'{code_prefix}.reference.outside-root',
                        f'reference escapes root: {ref}',
                    )
                )
                continue
        except OSError:
            diags.append(
                Diagnostic(
                    item_str,
                    v_id,
                    f'{code_prefix}.reference.invalid',
                    f'reference cannot be resolved: {ref}',
                )
            )
            continue
        if not target.exists():
            diags.append(
                Diagnostic(
                    item_str,
                    v_id,
                    f'{code_prefix}.reference.invalid',
                    f'referenced file does not exist: {ref}',
                )
            )
    return diags


def validate_skill_item(
    root: Path, file_path: Path, item_path: str, _item_name: str
) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    text = file_path.read_text(encoding='utf-8')
    lines = text.splitlines()
    if len(lines) > 500:
        diags.append(
            Diagnostic(
                item_path,
                'skill.structure',
                'skill.document.size',
                f'{len(lines)} lines exceeds 500 limit',
            )
        )
    try:
        meta, body = parse_frontmatter(text)
    except ValueError as exc:
        diags.append(
            Diagnostic(
                item_path,
                'skill.frontmatter',
                'skill.frontmatter.invalid',
                str(exc),
            )
        )
        return diags
    name = str(meta.get('name', '')).strip()
    desc = str(meta.get('description', '')).strip()
    if not name or not desc:
        diags.append(
            Diagnostic(
                item_path,
                'skill.frontmatter',
                'skill.metadata.missing',
                "missing 'name' or 'description'",
            )
        )
    if name and name != file_path.parent.name:
        diags.append(
            Diagnostic(
                item_path,
                'skill.frontmatter',
                'skill.metadata.name-mismatch',
                f"frontmatter name '{name}' != directory '{file_path.parent.name}'",
            )
        )
    status = str(meta.get('status', 'active')).strip()
    allowed = (
        ALLOWED_SKILL_ARCHIVED_FM
        if status == 'archived'
        else ALLOWED_SKILL_ACTIVE_FM
    )
    if set(meta) - allowed:
        diags.append(
            Diagnostic(
                item_path,
                'skill.frontmatter',
                'skill.frontmatter.invalid',
                f'extra frontmatter keys: {sorted(set(meta) - allowed)}',
            )
        )
    if not body.lstrip().startswith('# '):
        diags.append(
            Diagnostic(
                item_path,
                'skill.structure',
                'skill.document.structure',
                "body must start with '# <Title>'",
            )
        )
    if not re.search(r'^## Procedimento\s*$', body, re.M):
        diags.append(
            Diagnostic(
                item_path,
                'skill.structure',
                'skill.document.structure',
                "missing '## Procedimento'",
            )
        )
    if not re.search(r'^## Exemplos\s*$', body, re.M) or not re.search(
        r'Por qu[eê] não|Caso negativo|caso negativo', body
    ):
        diags.append(
            Diagnostic(
                item_path,
                'skill.structure',
                'skill.document.structure',
                "'## Exemplos' must contain negative case",
            )
        )
    if not re.search(r'^## Evals de trigger\s*$', body, re.M) or not re.search(
        r'[Nn]ão deve acionar|[Nn]ao deve acionar', body
    ):
        diags.append(
            Diagnostic(
                item_path,
                'skill.structure',
                'skill.document.structure',
                "'## Evals de trigger' must contain 'Não deve acionar'",
            )
        )
    if re.search(r'^## Quando usar\s*$', body, re.M):
        diags.append(
            Diagnostic(
                item_path,
                'skill.structure',
                'skill.document.structure',
                "forbidden '## Quando usar'",
            )
        )
    diags.extend(
        _check_declared_refs(
            root, file_path, text, 'skill.references', 'skill'
        )
    )
    return diags


def validate_agent_item(
    root: Path, file_path: Path, item_path: str, _item_name: str
) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    text = file_path.read_text(encoding='utf-8')
    try:
        meta, body = parse_frontmatter(text)
    except ValueError as exc:
        diags.append(
            Diagnostic(
                item_path,
                'agent.frontmatter',
                'agent.frontmatter.invalid',
                str(exc),
            )
        )
        return diags
    name = str(meta.get('name', '')).strip()
    desc = str(meta.get('description', '')).strip()
    if not name or not desc:
        diags.append(
            Diagnostic(
                item_path,
                'agent.frontmatter',
                'agent.metadata.missing',
                "missing 'name' or 'description'",
            )
        )
    expected_name = file_path.name.replace('.agent.md', '')
    if name and name != expected_name:
        diags.append(
            Diagnostic(
                item_path,
                'agent.frontmatter',
                'agent.metadata.name-mismatch',
                f"frontmatter name '{name}' != filename stem '{expected_name}'",
            )
        )
    if set(meta) - ALLOWED_AGENT_FM:
        diags.append(
            Diagnostic(
                item_path,
                'agent.frontmatter',
                'agent.frontmatter.invalid',
                f'extra frontmatter keys: {sorted(set(meta) - ALLOWED_AGENT_FM)}',
            )
        )
    agents_list = meta.get('agents', [])
    if isinstance(agents_list, list):
        diags.extend(
            Diagnostic(
                item_path,
                'agent.frontmatter',
                'agent.reference.missing',
                f"missing referenced agent '{subagent}'",
            )
            for subagent in agents_list
            if not (file_path.parent / f'{subagent}.agent.md').exists()
        )
    headings = {
        h.split(' — ')[0].strip()
        for h in re.findall(r'^##\s+(.+?)\s*$', body, re.M)
    }
    missing_sections = [
        s for s in AGENT_REQUIRED_SECTIONS if s not in headings
    ]
    if missing_sections:
        diags.append(
            Diagnostic(
                item_path,
                'agent.structure',
                'agent.document.structure',
                f'missing required sections: {missing_sections}',
            )
        )
    legacy_present = [s for s in AGENT_LEGACY_SECTIONS if s in headings]
    if legacy_present:
        diags.append(
            Diagnostic(
                item_path,
                'agent.structure',
                'agent.document.central-only-section',
                f'legacy central sections present: {legacy_present}',
            )
        )
    diags.extend(
        _check_declared_refs(
            root, file_path, text, 'agent.references', 'agent'
        )
    )
    return diags


def validate_workflow_item(
    root: Path, file_path: Path, item_path: str, _item_name: str
) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    text = file_path.read_text(encoding='utf-8')
    try:
        meta, body = parse_frontmatter(text)
    except ValueError as exc:
        diags.append(
            Diagnostic(
                item_path,
                'workflow.frontmatter',
                'workflow.frontmatter.invalid',
                str(exc),
            )
        )
        return diags
    name = str(meta.get('name', '')).strip()
    desc = str(meta.get('description', '')).strip()
    if not name or not desc:
        diags.append(
            Diagnostic(
                item_path,
                'workflow.frontmatter',
                'workflow.metadata.missing',
                "missing 'name' or 'description'",
            )
        )
    if set(meta) - ALLOWED_WORKFLOW_FM:
        diags.append(
            Diagnostic(
                item_path,
                'workflow.frontmatter',
                'workflow.frontmatter.invalid',
                f'extra frontmatter keys: {sorted(set(meta) - ALLOWED_WORKFLOW_FM)}',
            )
        )
    if not re.findall(r'^##\s+(.+?)\s*$', body, re.M) or not body.strip():
        diags.append(
            Diagnostic(
                item_path,
                'workflow.structure',
                'workflow.document.structure',
                'workflow must contain at least one level-two section',
            )
        )
    diags.extend(
        _check_declared_refs(
            root, file_path, text, 'workflow.references', 'workflow'
        )
    )
    return diags
