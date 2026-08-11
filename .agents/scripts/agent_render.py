#!/usr/bin/env python3
"""Shared rendering for agent prompts.

With the removal of ``*.manifest.json`` files, this module no longer
renders routing/escalation checklists. It provides frontmatter parsing
and a passthrough ``compile_body`` so that downstream sync scripts
continue to work unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / '.agents' / 'agents'


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


def compile_body(core_body: str) -> str:
    """Return the agent body as-is.

    Previously this re-inserted manifest-rendered checklists before
    Done When.  Now that manifests are gone the body is self-contained
    and needs no transformation.
    """
    return core_body.rstrip() + '\n'
