#!/usr/bin/env python3
"""Sync local OpenCode, Codex, Claude, and GitHub agent mirrors."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess  # nosec B404
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = Path(__file__).resolve().parent
AGENT_DIR = REPO_ROOT / '.agents' / 'agents'
CONFIG_AGENT_DIR = REPO_ROOT / '.gemini' / 'config' / 'agents'

spec = importlib.util.spec_from_file_location(
    'agent_render', SCRIPTS_ROOT / 'agent_render.py'
)
if spec and spec.loader:
    agent_render = importlib.util.module_from_spec(spec)
    sys.modules['agent_render'] = agent_render
    spec.loader.exec_module(agent_render)

OPENCODE_CONFIG_PATH = REPO_ROOT / 'opencode.json'
CLAUDE_AGENT_DIR = REPO_ROOT / '.claude' / 'agents'
GITHUB_AGENT_DIR = REPO_ROOT / '.github' / 'agents'
CODEX_SYNC_SCRIPT = REPO_ROOT / '.agents' / 'scripts' / 'sync-codex-agents.py'


def sanitize_json_like(text: str) -> str:
    return re.sub(r',\s*([\]}])', r'\1', text)


def read_json_file(path: Path) -> dict[str, object]:
    result = json.loads(sanitize_json_like(path.read_text(encoding='utf-8')))
    return result if isinstance(result, dict) else {}


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
            metadata[key.strip()] = value.strip('"\'')
    return metadata, match.group(2)


def collect_agents_data() -> dict[str, dict[str, object]]:
    configs: dict[str, dict[str, object]] = {}

    for path in sorted(AGENT_DIR.glob('*.agent.md')):
        agent_name = path.name.replace('.agent.md', '')
        source_text = path.read_text(encoding='utf-8')
        metadata, body = parse_frontmatter(source_text)
        match = re.match(r'---\n(.*?)\n---\n', source_text, re.S)
        raw_frontmatter = match.group(1) if match else ''
        compiled_body = agent_render.compile_body(body)

        raw_agents = metadata.get('agents', [])
        allowed_agents: list[str] = []
        if isinstance(raw_agents, list):
            allowed_agents = [
                item for item in raw_agents if isinstance(item, str)
            ]

        configs[agent_name] = {
            'name': agent_name,
            'description': metadata.get('description', ''),
            'mode': metadata.get('mode', 'all'),
            'prompt': compiled_body,
            'agents': allowed_agents,
            'raw_frontmatter': raw_frontmatter,
            'compiled_body': compiled_body,
        }

    return configs


def sync_json_config(
    path: Path,
    agents_config: dict[str, dict[str, object]],
    *,
    check: bool,
) -> tuple[list[str], list[str]]:
    config = read_json_file(path)
    agent_section = config.get('agent')
    if not isinstance(agent_section, dict):
        agent_section = {}
        config['agent'] = agent_section

    for stale_name in sorted(set(agent_section) - set(agents_config)):
        del agent_section[stale_name]

    for agent_name, payload in agents_config.items():
        current = agent_section.get(agent_name)
        if not isinstance(current, dict):
            current = {}
            agent_section[agent_name] = current

        current['description'] = payload['description']
        current['mode'] = payload['mode']
        current['prompt'] = payload['prompt']

        agents = payload['agents']
        if agents:
            current['agents'] = agents
        else:
            current.pop('agents', None)

    rendered = json.dumps(config, ensure_ascii=False, indent=2) + '\n'
    current_text = path.read_text(encoding='utf-8')
    if current_text == rendered:
        return [], []

    rel = str(path.relative_to(REPO_ROOT))
    if check:
        return [rel], []

    path.write_text(rendered, encoding='utf-8')
    return [rel], [rel]


def run_codex_sync(*, check: bool) -> tuple[list[str], list[str]]:
    cmd = [sys.executable, str(CODEX_SYNC_SCRIPT)]
    if check:
        cmd.append('--check')

    proc = subprocess.run(  # nosec B603
        cmd,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError('sync-codex-agents.py produced no output')

    payload = json.loads(stdout)
    stale = payload.get('stale', [])
    updated = payload.get('updated', [])
    if proc.returncode not in (0, 1):
        raise RuntimeError(
            proc.stderr.strip() or 'sync-codex-agents.py failed'
        )
    return stale, updated


GITHUB_TOOLS: dict[str, list[str]] = {
    'developer-engineer': [
        'vscode/getProjectSetupInfo',
        'vscode/installExtension',
        'vscode/runCommand',
        'vscode/askQuestions',
        'execute/getTerminalOutput',
        'execute/killTerminal',
        'execute/sendToTerminal',
        'execute/createAndRunTask',
        'execute/runInTerminal',
        'execute/runTests',
        'read/problems',
        'read/readFile',
        'read/viewImage',
        'read/terminalSelection',
        'read/terminalLastCommand',
        'agent',
        'edit/createDirectory',
        'edit/createFile',
        'edit/editFiles',
        'edit/rename',
        'search/changes',
        'search/codebase',
        'search/fileSearch',
        'search/listDirectory',
        'search/textSearch',
        'search/usages',
        'vscode.mermaid-chat-features/renderMermaidDiagram',
        'ms-python.python/getPythonEnvironmentInfo',
        'ms-python.python/getPythonExecutableCommand',
        'ms-python.python/installPythonPackage',
        'ms-python.python/configurePythonEnvironment',
        'todo',
    ],
    'security-engineer': [
        'vscode/getProjectSetupInfo',
        'vscode/runCommand',
        'vscode/askQuestions',
        'execute/testFailure',
        'execute/getTerminalOutput',
        'execute/killTerminal',
        'execute/sendToTerminal',
        'execute/createAndRunTask',
        'execute/runInTerminal',
        'execute/runTests',
        'read/problems',
        'read/readFile',
        'read/viewImage',
        'read/terminalSelection',
        'read/terminalLastCommand',
        'agent',
        'search/changes',
        'search/codebase',
        'search/fileSearch',
        'search/listDirectory',
        'search/textSearch',
        'search/usages',
        'web/fetch',
        'playwright/browser_click',
        'playwright/browser_close',
        'playwright/browser_console_messages',
        'playwright/browser_drag',
        'playwright/browser_evaluate',
        'playwright/browser_file_upload',
        'playwright/browser_fill_form',
        'playwright/browser_handle_dialog',
        'playwright/browser_hover',
        'playwright/browser_install',
        'playwright/browser_navigate',
        'playwright/browser_navigate_back',
        'playwright/browser_network_requests',
        'playwright/browser_press_key',
        'playwright/browser_resize',
        'playwright/browser_run_code',
        'playwright/browser_select_option',
        'playwright/browser_snapshot',
        'playwright/browser_tabs',
        'playwright/browser_take_screenshot',
        'playwright/browser_type',
        'playwright/browser_wait_for',
        'browser/openBrowserPage',
        'browser/readPage',
        'browser/screenshotPage',
        'browser/navigatePage',
        'browser/clickElement',
        'browser/dragElement',
        'browser/hoverElement',
        'browser/typeInPage',
        'browser/runPlaywrightCode',
        'browser/handleDialog',
        'vscode.mermaid-chat-features/renderMermaidDiagram',
        'ms-python.python/getPythonEnvironmentInfo',
        'ms-python.python/getPythonExecutableCommand',
        'todo',
    ],
}


def render_claude(payload: dict[str, object]) -> str:
    return (
        f'---\nname: {payload["name"]}\n'
        f'description: {payload["description"]}\n---\n'
        f'{payload["compiled_body"]}'
    )


def render_github(payload: dict[str, object]) -> str:
    agent_name = str(payload['name'])
    raw_front = str(payload['raw_frontmatter']).strip()
    raw_tools = payload.get('tools')
    tools = (
        raw_tools
        if isinstance(raw_tools, list)
        else GITHUB_TOOLS.get(agent_name, [])
    )
    if tools and 'tools:' not in raw_front:
        tools_formatted = (
            'tools:\n  [\n' + ''.join(f'    {t},\n' for t in tools) + '  ]'
        )
        raw_front = f'{raw_front}\n{tools_formatted}'
    return f'---\n{raw_front}\n---\n{payload["compiled_body"]}'


def sync_dir_mirror(
    target_dir: Path,
    suffix: str,
    render_fn,
    agents_config: dict[str, dict[str, object]],
    *,
    check: bool,
) -> tuple[list[str], list[str]]:
    target_dir.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    updated: list[str] = []
    expected: set[str] = set()

    for agent_name, payload in agents_config.items():
        content = render_fn(payload)
        output_path = target_dir / f'{agent_name}{suffix}'
        expected.add(output_path.name)
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

    for path in sorted(target_dir.iterdir()):
        if (
            path.is_file()
            and path.name.endswith(suffix)
            and path.name not in expected
        ):
            rel = str(path.relative_to(REPO_ROOT))
            stale.append(rel)
            if not check:
                path.unlink()
                updated.append(rel)

    return stale, updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Sync local OpenCode, Codex, Claude, and GitHub agent mirrors from .agents/agents.'
    )
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    agents_config = collect_agents_data()
    opencode_stale, opencode_updated = sync_json_config(
        OPENCODE_CONFIG_PATH,
        agents_config,
        check=args.check,
    )
    codex_stale, codex_updated = run_codex_sync(check=args.check)
    claude_stale, claude_updated = sync_dir_mirror(
        CLAUDE_AGENT_DIR,
        '.md',
        render_claude,
        agents_config,
        check=args.check,
    )
    github_stale, github_updated = sync_dir_mirror(
        GITHUB_AGENT_DIR,
        '.agent.md',
        render_github,
        agents_config,
        check=args.check,
    )

    stale = opencode_stale + codex_stale + claude_stale + github_stale
    updated = (
        opencode_updated + codex_updated + claude_updated + github_updated
    )

    payload = {
        'status': 'ok'
        if not stale
        else ('stale' if args.check else 'updated'),
        'checked': len(agents_config) * 3 + 1,
        'stale': stale,
        'updated': updated,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not stale or not args.check else 1


if __name__ == '__main__':
    raise SystemExit(main())
