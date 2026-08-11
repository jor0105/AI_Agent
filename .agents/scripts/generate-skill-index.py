#!/usr/bin/env python3
"""Script para gerar o índice de skills ativas (.agents/skill-index.md)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AGENTS_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = AGENTS_ROOT / 'skills'
INDEX_FILE = AGENTS_ROOT / 'skill-index.md'
SKIP_PARTS = {
    '__pycache__',
    'references',
    'assets',
    'scripts',
    'templates',
    'schemas',
    'data',
}


def parse_value(raw: str) -> object:
    raw = raw.strip().strip('"\'')
    if raw.startswith('[') and raw.endswith(']'):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [
            item.strip().strip('"\'')
            for item in inner.split(',')
            if item.strip()
        ]
    return raw


def _consume_multiline_value(
    lines: list[str],
    index: int,
) -> tuple[str, int]:
    paragraphs: list[str] = []
    current_paragraph: list[str] = []
    while index < len(lines):
        continuation = lines[index]
        if not continuation.startswith((' ', '\t')):
            break
        stripped = continuation.strip()
        if stripped:
            current_paragraph.append(stripped)
        elif current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []
        index += 1

    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))
    return '\n\n'.join(paragraphs), index


def parse_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding='utf-8')
    match = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if not match:
        raise ValueError(f'{path}: missing strict frontmatter')

    metadata: dict[str, object] = {}
    lines = match.group(1).splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.startswith((' ', '\t')) or ':' not in line:
            index += 1
            continue
        key, raw = line.split(':', 1)
        key = key.strip()
        value = raw.strip()

        if value in {'>', '|', '>-', '|-'}:
            metadata[key], index = _consume_multiline_value(lines, index + 1)
            continue

        metadata[key] = parse_value(raw)
        index += 1
    return metadata


def iter_skill_files() -> list[Path]:
    files = []
    for path in SKILLS_ROOT.rglob('SKILL.md'):
        rel_parts = path.relative_to(SKILLS_ROOT).parts
        if any(part in SKIP_PARTS for part in rel_parts):
            continue
        files.append(path)
    return sorted(files)


def collect_active_skills() -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    for path in iter_skill_files():
        metadata = parse_frontmatter(path)
        if metadata.get('status') == 'archived':
            continue

        rel = path.relative_to(AGENTS_ROOT)
        skills.append(
            {
                'name': str(metadata.get('name', path.parent.name)),
                'description': str(metadata.get('description', '')),
                'path': f'.agents/{rel.as_posix()}',
            }
        )
    return skills


def render_index(skills: list[dict[str, str]]) -> str:
    lines = [
        '# Skill Index',
        '',
        'Este arquivo e **gerado automaticamente** pelo script `.agents/scripts/generate-skill-index.py`.',
        'Ele lista apenas skills ativas; skills arquivadas ficam fora do roteamento.',
        'A listagem e geral: nenhuma skill e agrupada por owner.',
        '',
    ]

    for skill in sorted(skills, key=lambda item: item['name']):
        lines.append(f'- **[{skill["name"]}]({skill["path"]})**')
        if skill['description']:
            lines.append(f'  > {skill["description"]}')
    lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Generate or check the skill index.'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Fail if the checked-in index is stale.',
    )
    args = parser.parse_args()

    rendered = render_index(collect_active_skills())

    if args.check:
        current = (
            INDEX_FILE.read_text(encoding='utf-8')
            if INDEX_FILE.exists()
            else ''
        )
        if current != rendered:
            print(
                f'{INDEX_FILE} is stale. Run `.agents/scripts/generate-skill-index.py`.',
                file=sys.stderr,
            )
            return 1
        print(f'PASS: {INDEX_FILE} is up to date.')
        return 0

    INDEX_FILE.write_text(rendered, encoding='utf-8')
    print(
        f'Indice gerado em {INDEX_FILE} ({rendered.count("- **[")} skills ativas).'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
