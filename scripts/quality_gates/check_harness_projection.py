"""Verify the staged harness projection without relying on a global command."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from git_changes import (
    GitInspectionError,
    changed_records,
    repository_root,
    repository_snapshot,
)

LOCK_PATH = Path('.agents/harness.lock.json')
MANIFEST_PATH = Path('.agents/harness.json')
CATALOG_PATH = Path('.agents/harness/components.json')
HASH_PREFIX = 'sha256:'


class HarnessProjectionError(ValueError):
    """Raised when the materialized harness is incomplete or inconsistent."""


@dataclass(frozen=True)
class CatalogComponent:
    """One staged harness component and its declared dependencies."""

    source: str
    requires: tuple[str, ...]


def _read_json(path: Path) -> dict[str, Any]:
    """Read one object-shaped JSON file from an index snapshot."""
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as err:
        raise HarnessProjectionError(f'{path.as_posix()} is missing.') from err
    except (OSError, UnicodeError) as err:
        raise HarnessProjectionError(
            f'{path.as_posix()} could not be read: {err}.'
        ) from err
    except json.JSONDecodeError as err:
        raise HarnessProjectionError(
            f'{path.as_posix()} is invalid JSON: {err}.'
        ) from err
    if not isinstance(payload, dict):
        raise HarnessProjectionError(
            f'{path.as_posix()} must be a JSON object.'
        )
    return payload


def component_hash(source: Path) -> str:
    """Return the D14 component hash used by the harness lock contract."""
    if source.is_file():
        files = [source]
        root = source.parent
    elif source.is_dir():
        files = sorted(path for path in source.rglob('*') if path.is_file())
        root = source
    else:
        raise HarnessProjectionError(f'{source.as_posix()} is missing.')
    pairs: list[tuple[str, str]] = []
    for path in files:
        if '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        pairs.append((relative, digest))
    pairs.sort(key=lambda pair: pair[0].encode('utf-8'))
    serialized = ''.join(
        f'{relative}\n{digest}\n' for relative, digest in pairs
    )
    return HASH_PREFIX + hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _catalog_components(
    catalog: dict[str, Any],
) -> dict[str, CatalogComponent]:
    """Return validated component metadata from the staged catalog."""
    raw_components = catalog.get('components')
    if not isinstance(raw_components, dict):
        raise HarnessProjectionError('catalog components must be an object.')
    components: dict[str, CatalogComponent] = {}
    for component_id, metadata in raw_components.items():
        if not isinstance(component_id, str) or not isinstance(metadata, dict):
            raise HarnessProjectionError(
                'catalog contains an invalid component entry.'
            )
        source = metadata.get('source')
        source_path = Path(source) if isinstance(source, str) else None
        if (
            source_path is None
            or source_path.is_absolute()
            or '..' in source_path.parts
            or source_path.as_posix() != source
        ):
            raise HarnessProjectionError(
                f'catalog component {component_id!r} has an unsafe source path.'
            )
        requires = metadata.get('requires')
        if not isinstance(requires, list) or not all(
            isinstance(required, str) for required in requires
        ):
            raise HarnessProjectionError(
                f'catalog component {component_id!r} has invalid requires.'
            )
        components[component_id] = CatalogComponent(source, tuple(requires))
    return components


def _manifest_component_id(
    category: str,
    name: object,
    catalog: dict[str, CatalogComponent],
) -> str:
    """Return and validate the catalog identifier for one manifest entry."""
    if not isinstance(name, str):
        raise HarnessProjectionError(
            'harness manifest component names must be strings.'
        )
    component_id = (
        f'skills/{name}' if category == 'review' else f'{category}/{name}'
    )
    if component_id not in catalog:
        raise HarnessProjectionError(
            f'harness manifest selects unknown component {component_id!r}.'
        )
    return component_id


def _manifest_selection(
    manifest: dict[str, Any], catalog: dict[str, CatalogComponent]
) -> set[str]:
    """Return the validated component identifiers selected by the manifest."""
    raw_selection = manifest.get('components')
    if not isinstance(raw_selection, dict):
        raise HarnessProjectionError(
            'harness manifest components must be an object.'
        )
    selected: set[str] = set()
    for category, names in raw_selection.items():
        if not isinstance(category, str) or not isinstance(names, list):
            raise HarnessProjectionError(
                'harness manifest contains an invalid selection.'
            )
        for name in names:
            selected.add(_manifest_component_id(category, name, catalog))
    return selected


def _include_required_components(
    selected: set[str], catalog: dict[str, CatalogComponent]
) -> set[str]:
    """Expand a manifest selection to its complete dependency closure."""
    pending = list(selected)
    while pending:
        component_id = pending.pop()
        for required in catalog[component_id].requires:
            if required not in catalog:
                raise HarnessProjectionError(
                    f'{component_id} requires unknown component {required!r}.'
                )
            if required not in selected:
                selected.add(required)
                pending.append(required)
    return selected


def _selected_component_ids(
    manifest: dict[str, Any], catalog: dict[str, CatalogComponent]
) -> set[str]:
    """Resolve the manifest selection plus every catalog dependency edge."""
    return _include_required_components(
        _manifest_selection(manifest, catalog), catalog
    )


def _validate_lock_metadata(
    lock: dict[str, Any], manifest: dict[str, Any]
) -> tuple[list[str], set[str]]:
    """Validate lock metadata and return its normalized managed paths."""
    errors: list[str] = []
    central_version = lock.get('centralVersion')
    if not isinstance(central_version, str) or not central_version:
        errors.append('harness lock must declare a non-empty centralVersion.')
    elif manifest.get('version') != central_version:
        errors.append(
            'harness manifest version does not match lock centralVersion.'
        )

    managed = lock.get('managedPaths')
    if not isinstance(managed, list) or not all(
        isinstance(path, str) for path in managed
    ):
        errors.append('harness lock managedPaths must be a list of strings.')
        return errors, set()

    managed_paths = set(managed)
    if managed != sorted(managed) or len(managed_paths) != len(managed):
        errors.append('harness lock managedPaths must be sorted and unique.')
    return errors, managed_paths


def _validate_lock_component(
    snapshot: Path,
    entry: object,
    catalog: dict[str, CatalogComponent],
    managed_paths: set[str],
) -> tuple[str | None, list[str]]:
    """Validate one lock component and return its identifier and errors."""
    if not isinstance(entry, dict):
        return None, ['harness lock contains a non-object component entry.']

    component_id = entry.get('id')
    expected_hash = entry.get('hash')
    if not isinstance(component_id, str) or component_id not in catalog:
        return None, [
            f'harness lock references unknown component {component_id!r}.'
        ]
    if not isinstance(expected_hash, str) or not expected_hash.startswith(
        HASH_PREFIX
    ):
        return component_id, [
            f'{component_id}: lock hash must use the sha256: prefix.'
        ]

    projected_path = Path('.agents') / catalog[component_id].source
    if projected_path.as_posix() not in managed_paths:
        return component_id, [
            f'{component_id}: target is absent from managedPaths.'
        ]
    try:
        actual_hash = component_hash(snapshot / projected_path)
    except HarnessProjectionError as err:
        return component_id, [f'{component_id}: {err}']
    if actual_hash != expected_hash:
        return component_id, [
            f'{component_id}: projection hash differs from staged harness lock.'
        ]
    return component_id, []


def _validate_lock_components(
    snapshot: Path,
    entries: list[object],
    catalog: dict[str, CatalogComponent],
    managed_paths: set[str],
) -> tuple[list[str], list[str]]:
    """Validate every lock component while preserving declared order."""
    errors: list[str] = []
    component_ids: list[str] = []
    for entry in entries:
        component_id, component_errors = _validate_lock_component(
            snapshot, entry, catalog, managed_paths
        )
        errors.extend(component_errors)
        if component_id is not None:
            component_ids.append(component_id)
    return errors, component_ids


def _validate_projection_sets(
    snapshot: Path,
    component_ids: list[str],
    managed_paths: set[str],
    manifest: dict[str, Any],
    catalog: dict[str, CatalogComponent],
) -> list[str]:
    """Validate ordering and exact manifest, lock, and projection sets."""
    errors: list[str] = []
    if component_ids != sorted(component_ids) or len(
        set(component_ids)
    ) != len(component_ids):
        errors.append(
            'harness lock components must be sorted and unique by id.'
        )

    selected_ids = _selected_component_ids(manifest, catalog)
    if set(component_ids) != selected_ids:
        errors.append(
            'harness lock components do not match the manifest dependency closure.'
        )
    expected_managed = {'.agents/harness'} | {
        (Path('.agents') / catalog[component_id].source).as_posix()
        for component_id in selected_ids
    }
    if managed_paths != expected_managed:
        errors.append(
            'harness lock managedPaths do not exactly match selected targets.'
        )
    if not (snapshot / '.agents/harness').is_dir():
        errors.append('harness base directory is missing from the projection.')
    return errors


def validate_harness_projection(snapshot: Path) -> list[str]:
    """Return staged lock/projection discrepancies with no working-tree input."""
    lock = _read_json(snapshot / LOCK_PATH)
    manifest = _read_json(snapshot / MANIFEST_PATH)
    catalog = _catalog_components(_read_json(snapshot / CATALOG_PATH))
    errors, managed_paths = _validate_lock_metadata(lock, manifest)

    components = lock.get('components')
    if not isinstance(components, list):
        return [*errors, 'harness lock components must be a list.']
    component_errors, component_ids = _validate_lock_components(
        snapshot, components, catalog, managed_paths
    )
    errors.extend(component_errors)
    errors.extend(
        _validate_projection_sets(
            snapshot, component_ids, managed_paths, manifest, catalog
        )
    )
    return errors


def _is_harness_path(path: str) -> bool:
    return path == '.agents' or path.startswith('.agents/')


def _snapshot_errors(snapshot: Path) -> list[str]:
    if not (snapshot / LOCK_PATH).is_file():
        return ['.agents/harness.lock.json is missing from the snapshot.']
    return validate_harness_projection(snapshot)


def main(argv: list[str] | None = None) -> int:
    """Run the staged or exact-revision harness-projection gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', metavar='REV')
    args = parser.parse_args(argv)
    try:
        root = repository_root()
        if args.revision:
            with repository_snapshot(
                root, args.revision, scope='repository'
            ) as snapshot:
                errors = _snapshot_errors(snapshot)
        else:
            changes = changed_records(root, scope='repository')
            if not any(
                _is_harness_path(path)
                for change in changes
                for path in (change.old_path, change.new_path)
                if path is not None
            ):
                print('SKIP [HARNESS_PROJECTION]: No staged .agents changes.')
                return 0
            with repository_snapshot(root, scope='repository') as snapshot:
                errors = _snapshot_errors(snapshot)
    except (
        GitInspectionError,
        HarnessProjectionError,
        OSError,
        UnicodeError,
    ) as err:
        print(f'ERROR [HARNESS_PROJECTION]: {err}', file=sys.stderr)
        return 2
    if errors:
        print(
            'FAIL [HARNESS_PROJECTION]: Staged harness projection drifted:',
            file=sys.stderr,
        )
        for error in errors:
            print(f'  • {error}', file=sys.stderr)
        print(
            'Resolution: regenerate the projection through its approved harness '
            'workflow and stage the matching lock.',
            file=sys.stderr,
        )
        return 1
    print(
        'PASS [HARNESS_PROJECTION]: Staged harness projection matches its lock.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
