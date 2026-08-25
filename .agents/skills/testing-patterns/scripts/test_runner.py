#!/usr/bin/env python3
"""Conservative test command resolver for testing-patterns."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[union-attr]
except (AttributeError, OSError):
    pass


@dataclass(frozen=True)
class TestCommand:
    project_type: str
    framework: str
    command: list[str]
    coverage_command: list[str] | None
    reason: str


def load_package_json(project_path: Path) -> dict[str, Any]:
    package_json = project_path / 'package.json'
    if not package_json.exists():
        return {}
    try:
        payload = json.loads(package_json.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def detect_node_command(project_path: Path) -> TestCommand | None:
    package = load_package_json(project_path)
    if not package:
        return None

    scripts = package.get('scripts', {})
    dependencies = {
        **package.get('dependencies', {}),
        **package.get('devDependencies', {}),
    }
    if not isinstance(scripts, dict):
        scripts = {}
    if not isinstance(dependencies, dict):
        dependencies = {}

    if 'test' in scripts:
        coverage = None
        if 'test:coverage' in scripts:
            coverage = ['npm', 'run', 'test:coverage']
        elif 'vitest' in dependencies:
            coverage = ['npx', 'vitest', 'run', '--coverage']
        elif 'jest' in dependencies:
            coverage = ['npx', 'jest', '--coverage']
        return TestCommand(
            project_type='node',
            framework='npm test',
            command=['npm', 'test'],
            coverage_command=coverage,
            reason='package.json exposes a test script',
        )

    if 'vitest' in dependencies:
        return TestCommand(
            project_type='node',
            framework='vitest',
            command=['npx', 'vitest', 'run'],
            coverage_command=['npx', 'vitest', 'run', '--coverage'],
            reason='vitest dependency detected',
        )

    if 'jest' in dependencies:
        return TestCommand(
            project_type='node',
            framework='jest',
            command=['npx', 'jest'],
            coverage_command=['npx', 'jest', '--coverage'],
            reason='jest dependency detected',
        )

    return None


def detect_python_command(project_path: Path) -> TestCommand | None:
    has_pyproject = (project_path / 'pyproject.toml').exists()
    has_requirements = any(project_path.glob('requirements*.txt'))
    has_tests = (project_path / 'tests').is_dir()
    if not (has_pyproject or has_requirements or has_tests):
        return None

    prefix = ['uv', 'run'] if (project_path / 'uv.lock').exists() else []
    base = [*prefix, 'python', '-m', 'pytest']
    return TestCommand(
        project_type='python',
        framework='pytest',
        command=[*base, '-v'],
        coverage_command=[*base, '--cov', '--cov-report=term-missing'],
        reason='Python test surface detected',
    )


def detect_test_command(project_path: Path) -> TestCommand | None:
    # Prefer explicit Node test script; otherwise Python usually has the repo-native
    # command in pyproject/uv for this workspace style.
    node = detect_node_command(project_path)
    python = detect_python_command(project_path)
    if node and node.framework == 'npm test':
        return node
    return python or node


def parse_test_counts(output: str) -> dict[str, int]:
    passed = 0
    failed = 0
    skipped = 0
    passed_match = re.search(r'(\d+)\s+passed', output, re.I)
    failed_match = re.search(r'(\d+)\s+failed', output, re.I)
    skipped_match = re.search(r'(\d+)\s+skipped', output, re.I)
    if passed_match:
        passed = int(passed_match.group(1))
    if failed_match:
        failed = int(failed_match.group(1))
    if skipped_match:
        skipped = int(skipped_match.group(1))
    return {
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'total': passed + failed + skipped,
    }


def execute_test_command(
    command: list[str],
    cwd: Path,
    timeout: int,
) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {
            'status': 'blocked',
            'passed': False,
            'error': f'Command not found: {command[0]}',
            'stdout': '',
            'stderr': '',
            'counts': {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0},
        }
    except subprocess.TimeoutExpired:
        return {
            'status': 'timeout',
            'passed': False,
            'error': f'Timeout after {timeout}s',
            'stdout': '',
            'stderr': '',
            'counts': {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0},
        }

    combined = f'{proc.stdout}\n{proc.stderr}'
    return {
        'status': 'passed' if proc.returncode == 0 else 'failed',
        'passed': proc.returncode == 0,
        'returncode': proc.returncode,
        'error': '',
        'stdout': proc.stdout[:4000],
        'stderr': proc.stderr[:1000],
        'counts': parse_test_counts(combined),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Resolve and optionally run project-native tests.'
    )
    parser.add_argument(
        'project_path',
        nargs='?',
        default='.',
        help='Project directory to inspect.',
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Use the detected coverage command when available.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only print the detected command without running tests.',
    )
    parser.add_argument(
        '--output',
        choices=['summary', 'json'],
        default='summary',
        help='Output format.',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Test command timeout in seconds.',
    )
    return parser


def command_payload(
    project_path: Path,
    test_command: TestCommand | None,
    selected: list[str] | None,
    status: str,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        'script': 'test_runner',
        'project': str(project_path),
        'timestamp': datetime.now(UTC).isoformat(),
        'status': status,
        'project_type': test_command.project_type
        if test_command
        else 'unknown',
        'framework': test_command.framework if test_command else None,
        'reason': test_command.reason
        if test_command
        else 'No test command detected',
        'command': selected,
        'result': result,
    }


def print_summary(payload: dict[str, Any]) -> None:
    print('Testing patterns runner')
    print(f'Project: {payload["project"]}')
    print(f'Status: {payload["status"]}')
    print(f'Framework: {payload["framework"]}')
    print(f'Reason: {payload["reason"]}')
    if payload['command']:
        print(f'Command: {" ".join(payload["command"])}')
    result = payload.get('result')
    if not result:
        return
    print(f'Result: {result["status"]}')
    if result.get('error'):
        print(f'Error: {result["error"]}')
    counts = result.get('counts', {})
    if counts.get('total'):
        print(
            'Tests: '
            f'{counts["total"]} total, {counts["passed"]} passed, '
            f'{counts["failed"]} failed, {counts["skipped"]} skipped'
        )
    stdout = result.get('stdout') or ''
    if stdout:
        print('\n'.join(stdout.splitlines()[:30]))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(json.dumps({'error': f'Path not found: {project_path}'}))
        return 1
    if not project_path.is_dir():
        print(
            json.dumps({'error': f'Path is not a directory: {project_path}'})
        )
        return 1

    test_command = detect_test_command(project_path)
    if test_command is None:
        payload = command_payload(project_path, None, None, 'not_configured')
        if args.output == 'json':
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print_summary(payload)
        return 2

    selected = (
        test_command.coverage_command
        if args.coverage and test_command.coverage_command
        else test_command.command
    )
    if args.dry_run:
        payload = command_payload(
            project_path, test_command, selected, 'planned'
        )
        if args.output == 'json':
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print_summary(payload)
        return 0

    result = execute_test_command(selected, project_path, args.timeout)
    payload = command_payload(
        project_path,
        test_command,
        selected,
        result['status'],
        result=result,
    )
    if args.output == 'json':
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_summary(payload)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
