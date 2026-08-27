"""Parse the narrow pre-commit hook blocks needed by the policy gate."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HOOK_ID_RE = re.compile(r'^\s*-\s+id:\s*([A-Za-z0-9._-]+)\s*$')


@dataclass(frozen=True)
class _HookBlock:
    """One hook and its YAML lines, parsed without a YAML runtime."""

    hook_id: str
    lines: tuple[str, ...]

    def value(self, field: str) -> str:
        """Return one scalar or folded value from this hook's YAML block."""
        field_re = re.compile(
            rf'^(?P<indent>\s*){re.escape(field)}:\s*(?P<value>.*)$'
        )
        for index, line in enumerate(self.lines):
            match = field_re.match(line)
            if not match:
                continue
            value = match.group('value').strip()
            if value not in {'>', '>-', '|', '|-'}:
                return value
            indent = len(match.group('indent'))
            continuation: list[str] = []
            for following in self.lines[index + 1 :]:
                if not following.strip():
                    continue
                leading = len(following) - len(following.lstrip())
                if leading <= indent:
                    break
                continuation.append(following.strip())
            return ' '.join(continuation)
        return ''

    def entry(self) -> str:
        """Return the command from this hook's ``entry`` field."""
        return self.value('entry')


def _parse_hook_blocks(content: str) -> dict[str, _HookBlock]:
    """Return hooks indexed by id, rejecting ambiguous duplicate ids."""
    blocks: dict[str, _HookBlock] = {}
    current_id: str | None = None
    current_lines: list[str] = []

    def finish() -> None:
        if current_id is None:
            return
        if current_id in blocks:
            raise ValueError(f'duplicate hook id {current_id!r}')
        blocks[current_id] = _HookBlock(current_id, tuple(current_lines))

    for line in content.splitlines():
        match = _HOOK_ID_RE.match(line)
        if match:
            finish()
            current_id = match.group(1)
            current_lines = [line]
        elif current_id is not None:
            current_lines.append(line)
    finish()
    return blocks
