"""Deterministic evidence snapshots for isolated consumer validation."""

from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

from harness import consumer_validation_evidence_schema as _schema
from harness import consumer_validation_snapshot as _snapshot
from harness.consumer_types import ContractError
from harness.consumer_validation import verify_path_confinement

CHECK_SCHEMA_VERSION = _schema.CHECK_SCHEMA_VERSION
CURRENT_PROFILE = _schema.CURRENT_PROFILE
CURRENT_PROTOCOL_VERSION = _schema.CURRENT_PROTOCOL_VERSION
PROFILE_COMPATIBILITY_REGISTRY = _schema.PROFILE_COMPATIBILITY_REGISTRY
PROFILE_REGISTRY = _schema.PROFILE_REGISTRY
PROTOCOL_COMPATIBILITY_REGISTRY = _schema.PROTOCOL_COMPATIBILITY_REGISTRY
PROTOCOL_REGISTRY = _schema.PROTOCOL_REGISTRY
SNAPSHOT_COMPATIBILITY_REGISTRY = _schema.SNAPSHOT_COMPATIBILITY_REGISTRY
SNAPSHOT_DATA_PARSERS = _schema.SNAPSHOT_DATA_PARSERS
SNAPSHOT_FIELDS = _schema.SNAPSHOT_FIELDS
SNAPSHOT_REGISTRY = _schema.SNAPSHOT_REGISTRY
SNAPSHOT_VERSION = _schema.SNAPSHOT_VERSION
CompatibilityEntry = _schema.CompatibilityEntry
is_valid_snapshot_document = _schema.is_valid_snapshot_document
normalized_request = _schema.normalized_request
override_compatibility_registries = _schema.override_compatibility_registries
request_identity = _schema.request_identity
temporary_registry_override = _schema.temporary_registry_override
validate_snapshot_document = _schema.validate_snapshot_document
EVIDENCE_VALIDATOR_ID = _snapshot.EVIDENCE_VALIDATOR_ID
SNAPSHOT_RELATIVE_PATH = _snapshot.SNAPSHOT_RELATIVE_PATH
SnapshotCheck = _snapshot.SnapshotCheck
SnapshotReadError = _snapshot.SnapshotReadError
snapshot_from_result = _snapshot.snapshot_from_result


class SnapshotWriteError(ContractError):
    """The deterministic snapshot could not be published atomically."""


def serialize_snapshot(snapshot: dict[str, Any]) -> bytes:
    """Serialize a validated snapshot with exactly one final LF."""
    validate_snapshot_document(snapshot)
    return _schema.serialize_canonical(snapshot)


def snapshot_path(root: Path) -> Path:
    """Resolve the fixed snapshot target while enforcing root confinement."""
    return verify_path_confinement(
        root, SNAPSHOT_RELATIVE_PATH, 'snapshot path', must_exist=False
    )


def _new_parent_dirs(parent: Path) -> list[Path]:
    missing: list[Path] = []
    cursor = parent
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    created: list[Path] = []
    for directory in reversed(missing):
        directory.mkdir()
        created.append(directory)
    return created


def _remove_empty_dirs(directories: list[Path]) -> None:
    for directory in reversed(directories):
        try:
            directory.rmdir()
        except OSError:
            break


def write_snapshot(root: Path, snapshot: dict[str, Any]) -> bytes:
    """Atomically publish a deterministic snapshot beneath the Git root."""
    target = snapshot_path(root)
    payload = serialize_snapshot(snapshot)
    created: list[Path] = []
    temporary: Path | None = None
    try:
        created = _new_parent_dirs(target.parent)
        fd, name = tempfile.mkstemp(
            prefix='.snapshot.', suffix='.tmp', dir=target.parent
        )
        temporary = Path(name)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        temporary = None
    except OSError as exc:
        if temporary is not None:
            with suppress(OSError):
                temporary.unlink()
        _remove_empty_dirs(created)
        raise SnapshotWriteError(
            f'cannot atomically publish {SNAPSHOT_RELATIVE_PATH}: {exc}'
        ) from exc
    return payload


def publish_snapshot(
    root: Path, request_data: dict[str, Any], result: dict[str, Any]
) -> bytes:
    """Build and atomically publish a snapshot for a passing result."""
    return write_snapshot(root, snapshot_from_result(request_data, result))


def check_snapshot(
    root: Path, request_data: dict[str, Any], result: dict[str, Any]
) -> SnapshotCheck:
    """Classify existing evidence without writing or invoking old executors."""
    return _snapshot.check_snapshot(root, request_data, result)
