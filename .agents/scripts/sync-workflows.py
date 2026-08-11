#!/usr/bin/env python3
"""Sync local workflow mirrors from .agents/workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / '.agents' / 'workflows'
GITHUB_PROMPTS_DIR = REPO_ROOT / '.github' / 'prompts'
OPENCODE_COMMANDS_DIR = REPO_ROOT / '.opencode' / 'commands'
CLAUDE_COMMANDS_DIR = REPO_ROOT / '.claude' / 'commands'


def collect_sources() -> tuple[dict[str, str], dict[str, str]]:
    github_rendered: dict[str, str] = {}
    opencode_rendered: dict[str, str] = {}

    for source_path in sorted(
        path for path in WORKFLOWS_DIR.iterdir() if path.is_file()
    ):
        content = source_path.read_text(encoding='utf-8')
        github_rendered[source_path.name] = content

        target_name = (
            source_path.name.replace('.prompt.md', '.md')
            if source_path.name.endswith('.prompt.md')
            else source_path.name
        )
        opencode_rendered[target_name] = content

    return github_rendered, opencode_rendered


def sync_directory(
    target_dir: Path,
    rendered: dict[str, str],
    *,
    check: bool,
) -> tuple[list[str], list[str]]:
    target_dir.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    updated: list[str] = []

    for name, content in rendered.items():
        output_path = target_dir / name
        current = (
            output_path.read_text(encoding='utf-8')
            if output_path.exists()
            else None
        )
        if current != content:
            rel = str(output_path.relative_to(REPO_ROOT))
            stale.append(rel)
            if not check:
                output_path.write_text(content, encoding='utf-8')
                updated.append(rel)

    expected = set(rendered)
    for path in sorted(target_dir.iterdir()):
        if path.is_file() and path.name not in expected:
            rel = str(path.relative_to(REPO_ROOT))
            stale.append(rel)
            if not check:
                path.unlink()
                updated.append(rel)

    return stale, updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Sync local GitHub prompts, OpenCode commands, and Claude commands from .agents/workflows.'
    )
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    github_rendered, opencode_rendered = collect_sources()
    github_stale, github_updated = sync_directory(
        GITHUB_PROMPTS_DIR,
        github_rendered,
        check=args.check,
    )
    opencode_stale, opencode_updated = sync_directory(
        OPENCODE_COMMANDS_DIR,
        opencode_rendered,
        check=args.check,
    )
    claude_stale, claude_updated = sync_directory(
        CLAUDE_COMMANDS_DIR,
        opencode_rendered,
        check=args.check,
    )

    stale = github_stale + opencode_stale + claude_stale
    updated = github_updated + opencode_updated + claude_updated
    payload = {
        'status': 'ok'
        if not stale
        else ('stale' if args.check else 'updated'),
        'checked': len(github_rendered)
        + len(opencode_rendered)
        + len(opencode_rendered),
        'stale': stale,
        'updated': updated,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not stale or not args.check else 1


if __name__ == '__main__':
    raise SystemExit(main())
