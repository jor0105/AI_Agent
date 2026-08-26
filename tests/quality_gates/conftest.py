"""Make the project-owned quality gate scripts importable in their tests."""

from __future__ import annotations

import sys
from pathlib import Path

QUALITY_GATES = (
    Path(__file__).resolve().parents[2] / 'scripts' / 'quality_gates'
)
sys.path.insert(0, str(QUALITY_GATES))
