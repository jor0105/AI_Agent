#!/usr/bin/env python3
"""Auto Preview - Antigravity Kit.

Manages (start/stop/status) the local development server for previewing the application.

Usage:
    python .agents/skills/server-management/scripts/auto_preview.py start [port]
    python .agents/skills/server-management/scripts/auto_preview.py stop
    python .agents/skills/server-management/scripts/auto_preview.py status
"""

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

AGENT_DIR = Path('.agents')
PID_FILE = AGENT_DIR / 'preview.pid'
LOG_FILE = AGENT_DIR / 'preview.log'
INFO_ICON = '\N{INFORMATION SOURCE}\N{VARIATION SELECTOR-16}'


def get_project_root() -> Path:
    return Path().resolve()


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def get_start_command(root: Path) -> list[str] | None:
    pkg_file = root / 'package.json'
    if not pkg_file.exists():
        return None

    try:
        with open(pkg_file, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    scripts = data.get('scripts', {})
    if not isinstance(scripts, dict):
        return None

    if 'dev' in scripts:
        return ['npm', 'run', 'dev']
    if 'start' in scripts:
        return ['npm', 'start']
    return None


def start_server(port: int = 3000) -> None:
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if is_running(pid):
                print(f'⚠️  Preview already running (PID: {pid})')
                return
        except (ValueError, OSError):
            pass  # Invalid PID file

    root = get_project_root()
    cmd = get_start_command(root)

    if not cmd:
        print("❌ No 'dev' or 'start' script found in package.json")
        sys.exit(1)

    # Add port env var if needed (simple heuristic)
    env = os.environ.copy()
    env['PORT'] = str(port)

    print(f'🚀 Starting preview on port {port}...')

    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        process = subprocess.Popen(
            cmd,
            cwd=str(root),
            stdout=log,
            stderr=log,
            env=env,
        )

    PID_FILE.write_text(str(process.pid))
    print(f'✅ Preview started! (PID: {process.pid})')
    print(f'   Logs: {LOG_FILE}')
    print(f'   URL: http://localhost:{port}')


def stop_server() -> None:
    if not PID_FILE.exists():
        print(f'{INFO_ICON}  No preview server found.')
        return

    try:
        pid = int(PID_FILE.read_text().strip())
        if is_running(pid):
            # Try gentle kill first
            os.kill(
                pid, signal.SIGTERM
            ) if sys.platform != 'win32' else subprocess.call(
                ['taskkill', '/F', '/T', '/PID', str(pid)]
            )
            print(f'🛑 Preview stopped (PID: {pid})')
        else:
            print(f'{INFO_ICON}  Process was not running.')
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        print(f'❌ Error stopping server: {e}')
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()


def status_server() -> None:
    running = False
    pid = None
    url = 'Unknown'

    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if is_running(pid):
                running = True
                # Heuristic for URL, strictly we should save it
                url = 'http://localhost:3000'
        except (ValueError, OSError):
            pass

    print('\n=== Preview Status ===')
    if running:
        print('✅ Status: Running')
        print(f'🔢 PID: {pid}')
        print(f'🌐 URL: {url} (Likely)')
        print(f'📝 Logs: {LOG_FILE}')
    else:
        print('⚪ Status: Stopped')
    print('===================\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'stop', 'status'])
    parser.add_argument('port', nargs='?', default='3000')

    args = parser.parse_args()

    if args.action == 'start':
        start_server(int(args.port))
    elif args.action == 'stop':
        stop_server()
    elif args.action == 'status':
        status_server()


if __name__ == '__main__':
    main()
