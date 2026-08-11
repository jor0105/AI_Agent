#!/usr/bin/env python3
"""Gera ou verifica os artifacts .codex/agents a partir dos prompts Markdown."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = Path(__file__).resolve().parent
AGENT_DIR = REPO_ROOT / '.agents' / 'agents'
CODEX_AGENT_DIR = REPO_ROOT / '.codex' / 'agents'

spec = importlib.util.spec_from_file_location(
    'agent_render', SCRIPTS_ROOT / 'agent_render.py'
)
if spec and spec.loader:
    agent_render = importlib.util.module_from_spec(spec)
    sys.modules['agent_render'] = agent_render
    spec.loader.exec_module(agent_render)
EXPECTED_AGENT_MODES: dict[str, str] = {}


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = re.match(r'---\n(.*?)\n---\n(.*)\Z', text, re.S)
    if not match:
        raise ValueError('missing frontmatter')

    metadata: dict[str, object] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith((' ', '\t')) or ':' not in line:
            continue
        key, raw_value = line.split(':', 1)
        value = raw_value.strip()
        if value.startswith('[') and value.endswith(']'):
            inner = value[1:-1].strip()
            metadata[key.strip()] = [
                item.strip().strip('"\'')
                for item in inner.split(',')
                if item.strip()
            ]
        else:
            lowered = value.lower()
            if lowered == 'true':
                metadata[key.strip()] = True
            elif lowered == 'false':
                metadata[key.strip()] = False
            else:
                metadata[key.strip()] = value.strip('"\'')
    return metadata, match.group(2)


def expected_mode_for(agent_name: str) -> str:
    return EXPECTED_AGENT_MODES.get(agent_name, 'all')


def infer_sandbox_mode(metadata: dict[str, object], body: str) -> str:
    explicit = metadata.get('sandbox_mode')
    if explicit in {'read-only', 'workspace-write', 'danger-full-access'}:
        return str(explicit)

    combined = f'{metadata.get("description", "")}\n{body}'.lower()
    read_only_markers = (
        'nunca edita codigo',
        'voce nao edita codigo',
        'editar codigo-fonte',
        'voce nao implementa, nao revisa diff como owner final',
        'voce nao implementa a correcao como owner principal',
    )
    if any(marker in combined for marker in read_only_markers):
        return 'read-only'
    return 'workspace-write'


def render_toml(
    agent_name: str, metadata: dict[str, object], body: str
) -> str:
    description = metadata.get('description')
    mode = metadata.get('mode')
    user_invocable = metadata.get('user-invocable', True)
    sandbox_mode = infer_sandbox_mode(metadata, body)

    if not isinstance(description, str) or not description:
        raise ValueError(f'{agent_name}: missing description')
    if not isinstance(mode, str) or not mode:
        raise ValueError(f'{agent_name}: missing mode')
    expected_mode = expected_mode_for(agent_name)
    if mode != expected_mode:
        raise ValueError(
            f"{agent_name}: invalid mode '{mode}', expected '{expected_mode}'"
        )
    if "'''" in body:
        raise ValueError(
            f'{agent_name}: prompt body contains unsupported triple single quote'
        )

    body = body.rstrip() + '\n'

    lines = [
        f'# Generated from .agents/agents/{agent_name}.agent.md.',
        '# Keep the source Markdown and this Codex-native TOML in sync when changing agent behavior.',
        f'name = "{agent_name}"',
        f'description = "{description}"',
        f'sandbox_mode = "{sandbox_mode}"',
        '',
        f'# Original agent metadata: mode={mode}, user_invocable={str(bool(user_invocable)).lower()}.',
        "developer_instructions = '''",
        body.rstrip('\n'),
        "'''",
        '',
    ]
    return '\n'.join(lines)


def collect_markdown_sources() -> dict[str, str]:
    rendered: dict[str, str] = {}
    for path in sorted(AGENT_DIR.glob('*.agent.md')):
        agent_name = path.name.replace('.agent.md', '')
        metadata, body = parse_frontmatter(path.read_text(encoding='utf-8'))
        compiled = agent_render.compile_body(body)
        rendered[agent_name] = render_toml(agent_name, metadata, compiled)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Sync .codex/agents from .agents/agents Markdown.'
    )
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    rendered = collect_markdown_sources()
    CODEX_AGENT_DIR.mkdir(parents=True, exist_ok=True)

    stale: list[str] = []
    updated: list[str] = []

    for agent_name, content in rendered.items():
        output_path = CODEX_AGENT_DIR / f'{agent_name}.toml'
        current = (
            output_path.read_text(encoding='utf-8')
            if output_path.exists()
            else None
        )
        if current != content:
            stale.append(str(output_path.relative_to(REPO_ROOT)))
            if not args.check:
                output_path.write_text(content, encoding='utf-8')
                updated.append(str(output_path.relative_to(REPO_ROOT)))

    expected = {f'{agent_name}.toml' for agent_name in rendered}
    for path in sorted(CODEX_AGENT_DIR.iterdir()):
        if path.is_file() and path.name not in expected:
            stale.append(str(path.relative_to(REPO_ROOT)))
            if not args.check:
                path.unlink()
                updated.append(str(path.relative_to(REPO_ROOT)))

    payload = {
        'status': 'ok'
        if not stale
        else ('stale' if args.check else 'updated'),
        'checked': len(rendered),
        'stale': stale,
        'updated': updated,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not stale or not args.check else 1


if __name__ == '__main__':
    raise SystemExit(main())
