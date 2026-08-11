#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"
repo_root="$(cd "${skill_dir}/../../.." && pwd)"

skill_file="${skill_dir}/SKILL.md"
command_map="${skill_dir}/references/COMMAND_MAP.md"
guardrails="${skill_dir}/references/GUARDRAILS.md"
evals="${skill_dir}/references/EVALS.md"

expected_commands=(
  "new"
  "continue"
  "apply"
  "verify"
  "sync"
  "archive"
  "bulk-archive"
  "explore"
  "ff"
  "onboard"
)

required_files=(
  "${skill_file}"
  "${command_map}"
  "${guardrails}"
  "${evals}"
)

description_text="$(
  python3 - "${skill_file}" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding='utf-8')
match = re.match(r'---\n(.*?)\n---\n', text, re.S)
if not match:
    raise SystemExit('frontmatter missing')

frontmatter = match.group(1)
description_lines: list[str] = []
collecting = False
for line in frontmatter.splitlines():
    if line.startswith('description:'):
        collecting = True
        _, _, value = line.partition(':')
        value = value.strip()
        if value != '>':
            description_lines.append(value)
        continue
    if collecting:
        if line.startswith((' ', '\t')):
            description_lines.append(line.strip())
            continue
        break

print(' '.join(description_lines))
PY
)"

for file in "${required_files[@]}"; do
  if [[ ! -f "${file}" ]]; then
    echo "Missing required file: ${file}" >&2
    exit 1
  fi
done

for command in "${expected_commands[@]}"; do
  workflow="${repo_root}/.agents/workflows/opsx-${command}.prompt.md"
  github_mirror="${repo_root}/.github/prompts/opsx-${command}.prompt.md"
  opencode_mirror="${repo_root}/.opencode/commands/opsx-${command}.md"
  token="/opsx:${command}"

  if [[ ! -f "${workflow}" ]]; then
    echo "Missing workflow: ${workflow}" >&2
    exit 1
  fi

  if [[ ! -f "${github_mirror}" ]]; then
    echo "Missing workflow mirror: ${github_mirror}" >&2
    exit 1
  fi

  if [[ ! -f "${opencode_mirror}" ]]; then
    echo "Missing workflow mirror: ${opencode_mirror}" >&2
    exit 1
  fi

  if ! cmp -s "${workflow}" "${github_mirror}"; then
    echo "Mirror drift detected for ${token} in GitHub mirror" >&2
    exit 1
  fi

  if ! cmp -s "${workflow}" "${opencode_mirror}"; then
    echo "Mirror drift detected for ${token} in OpenCode mirror" >&2
    exit 1
  fi

  if ! grep -F -q "${token}" "${skill_file}"; then
    echo "Command token missing from skill: ${token}" >&2
    exit 1
  fi

  if [[ "${description_text}" != *"${token}"* ]]; then
    echo "Command token missing from skill description: ${token}" >&2
    exit 1
  fi

  if ! grep -F -q "${token}" "${command_map}"; then
    echo "Command token missing from command map: ${token}" >&2
    exit 1
  fi
done

if grep -r -n -E 'openspec/changes/[^[:space:]`"'"'"'<>*]+\.md' "${skill_dir}"; then
  echo "Forbidden legacy execution pattern found in openspec-workflow skill" >&2
  exit 1
fi

echo "opsx alignment ok"
