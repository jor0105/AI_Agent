#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
harness_root="$(cd "${script_dir}/.." && pwd)"
repo_root="$(
  git -C "${script_dir}" rev-parse --show-toplevel 2>/dev/null ||
    printf '%s\n' "${harness_root}"
)"
skill_prefix="skills"
wf_prefix="workflows"
content_root="${harness_root}"
if [[ ! -d "${content_root}/${skill_prefix}/openspec-workflow" &&
  -d "${harness_root}/.agents/${skill_prefix}/openspec-workflow" ]]; then
  content_root="${harness_root}/.agents"
fi
skill_dir="${content_root}/${skill_prefix}/openspec-workflow"

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
  "explore"
  "ff"
)

forbidden_interaction_tokens=(
  "AskUserQuestion"
  "TodoWrite"
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
  workflow="${content_root}/${wf_prefix}/opsx-${command}.prompt.md"
  github_mirror="${repo_root}/.github/prompts/opsx-${command}.prompt.md"
  opencode_mirror="${repo_root}/.opencode/commands/opsx-${command}.md"
  claude_mirror="${repo_root}/.claude/commands/opsx-${command}.md"
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

  if [[ ! -f "${claude_mirror}" ]]; then
    echo "Missing workflow mirror: ${claude_mirror}" >&2
    exit 1
  fi

  if ! cmp -s "${workflow}" "${github_mirror}"; then
    echo "Mirror drift detected for ${token} in GitHub mirror: ${github_mirror}" >&2
    exit 1
  fi

  if ! cmp -s "${workflow}" "${opencode_mirror}"; then
    echo "Mirror drift detected for ${token} in OpenCode mirror: ${opencode_mirror}" >&2
    exit 1
  fi

  if ! cmp -s "${workflow}" "${claude_mirror}"; then
    echo "Mirror drift detected for ${token} in Claude mirror: ${claude_mirror}" >&2
    exit 1
  fi

  for consumer in "${workflow}" "${github_mirror}" "${opencode_mirror}" "${claude_mirror}"; do
    for forbidden_token in "${forbidden_interaction_tokens[@]}"; do
      if grep -F -q -- "${forbidden_token}" "${consumer}"; then
        echo "Forbidden harness-specific interaction '${forbidden_token}' found in ${consumer}" >&2
        exit 1
      fi
    done
  done

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

python3 - "${content_root}/agents/developer-engineer.agent.md" \
  "${content_root}/${wf_prefix}/opsx-"*.prompt.md \
  "${repo_root}/.github/prompts/opsx-"*.prompt.md \
  "${repo_root}/.opencode/commands/opsx-"*.md \
  "${repo_root}/.claude/commands/opsx-"*.md <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

automated_model_action = re.compile(
    r'\b(?:select|recommend|infer|rank|switch|choose|pick|classif(?:y|ies)|'
    r'request|solicit)\w*\b.{0,80}\bmodel(?:\s+metadata)?\b',
    re.IGNORECASE,
)
provider_model_name = re.compile(
    r'\b(?:gpt-\d[\w.-]*|claude-(?:\d[\w.-]*)|'
    r'(?:claude|gemini)\s+(?:sonnet|opus|haiku|pro|flash)|'
    r'o[134](?:-[\w.-]+)?|llama-\d[\w.-]*)\b',
    re.IGNORECASE,
)
manual_markers = (
    'do not', 'does not', 'must not', 'never', 'no model', 'manual',
    'user-selected', 'user selected', 'not select', 'not recommend',
    'not infer', 'not rank', 'not switch', 'not request', 'não', 'nao',
    'sem modelo',
)

for raw_path in sys.argv[1:]:
    path = Path(raw_path)
    for line_number, line in enumerate(
        path.read_text(encoding='utf-8').splitlines(), start=1
    ):
        lowered = line.lower()
        if any(marker in lowered for marker in manual_markers):
            continue
        if automated_model_action.search(line):
            raise SystemExit(
                f'Forbidden automated model-selection policy in {path}:{line_number}'
            )
        if provider_model_name.search(line):
            raise SystemExit(
                f'Forbidden provider model name in {path}:{line_number}'
            )
PY

require_workflow_text() {
  local workflow="$1"
  local expected="$2"
  if ! grep -F -q -- "${expected}" "${workflow}"; then
    echo "Required lifecycle contract missing from ${workflow}: ${expected}" >&2
    exit 1
  fi
}

require_workflow_text "${content_root}/${wf_prefix}/opsx-continue.prompt.md" \
  'Create exactly one artifact per invocation.'
require_workflow_text "${content_root}/${wf_prefix}/opsx-continue.prompt.md" \
  'injected rules take precedence over minimal examples'
require_workflow_text "${content_root}/${wf_prefix}/opsx-apply.prompt.md" \
  'opsx-handoff --mode bundle "<name>"'
require_workflow_text "${content_root}/${wf_prefix}/opsx-apply.prompt.md" \
  'evidence/gate-report.json'
require_workflow_text "${content_root}/${wf_prefix}/opsx-apply.prompt.md" \
  'opsx-handoff --mode apply "<name>"'
require_workflow_text "${content_root}/${wf_prefix}/opsx-sync.prompt.md" \
  'opsx-sync --change "<name>" --json'
require_workflow_text "${content_root}/${wf_prefix}/opsx-archive.prompt.md" \
  'an interactive override'
require_workflow_text "${content_root}/${wf_prefix}/opsx-explore.prompt.md" \
  'Explore mode is read-only.'
# Consumer-side contracts are deliberately absent here. A consuming project
# owns its own openspec/config.yaml, its validation command and its evidence
# verifier; the harness cannot assert on a repository it does not ship. What
# it can prove is that every command its workflows name is exposed by this
# package.
require_workflow_text "${repo_root}/pyproject.toml" \
  'opsx = "harness.opsx:main"'
require_workflow_text "${repo_root}/pyproject.toml" \
  'opsx-handoff = "harness.handoff:main"'
require_workflow_text "${repo_root}/pyproject.toml" \
  'opsx-sync = "harness.sync_specs:main"'
require_workflow_text "${repo_root}/pyproject.toml" \
  'sabatina = "harness.sabatina:main"'

if grep -r -n -E 'openspec/changes/[^[:space:]`"'"'"'<>*]+\.md' "${skill_dir}"; then
  echo "Forbidden legacy execution pattern found in openspec-workflow skill" >&2
  exit 1
fi

echo "opsx alignment ok"
