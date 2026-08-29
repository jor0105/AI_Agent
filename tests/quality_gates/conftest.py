"""Make the project-owned quality gate scripts importable in their tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

QUALITY_GATES = (
    Path(__file__).resolve().parents[2] / 'scripts' / 'quality_gates'
)
sys.path.insert(0, str(QUALITY_GATES))


@pytest.fixture(autouse=True)
def isolate_outer_git_index(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep temporary repositories independent of an outer hook index."""
    monkeypatch.delenv('GIT_INDEX_FILE', raising=False)
