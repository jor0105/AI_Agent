#!/usr/bin/env python3
"""Initialize a canonical review session."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[3] / 'runtime' / 'review')
)

from runtime_support import (
    CURRENT_SCHEMA_VERSION,
    build_default_verdict,
    build_empty_gate_report,
    build_empty_plan,
    ensure_session_layout,
    make_review_id,
    normalize_paths,
    now_iso,
    resolve_session_dir,
    save_artifact,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Initialize a canonical review session.'
    )
    parser.add_argument('--review-id', default=None)
    parser.add_argument('--session-dir', default=None)
    parser.add_argument('--change-type', required=True)
    parser.add_argument('--changed-by', required=True)
    parser.add_argument(
        '--security-touch', choices=['yes', 'no', 'auto'], default='auto'
    )
    parser.add_argument('--base-ref', default=None)
    parser.add_argument('--head-ref', default=None)
    parser.add_argument('--changed-file', action='append', default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    review_id = args.review_id or make_review_id()
    session_dir = resolve_session_dir(
        review_id=review_id, session_dir=args.session_dir
    )
    ensure_session_layout(session_dir)

    changed_files = normalize_paths(args.changed_file)
    stamp = now_iso()
    session = {
        'artifactType': 'review-session',
        'schemaVersion': CURRENT_SCHEMA_VERSION,
        'reviewId': review_id,
        'status': 'initialized',
        'createdAt': stamp,
        'updatedAt': stamp,
        'change': {
            'changeType': args.change_type,
            'changedBy': args.changed_by,
            'securityTouch': args.security_touch,
            'baseRef': args.base_ref,
            'headRef': args.head_ref,
        },
        'changedFiles': changed_files,
        'statistics': {
            'totalItems': 0,
            'completedItems': 0,
            'findingCount': 0,
            'blockingFindingCount': 0,
        },
    }

    save_artifact(session_dir, session)
    save_artifact(session_dir, build_empty_plan(review_id))
    save_artifact(session_dir, build_empty_gate_report(review_id))
    save_artifact(session_dir, build_default_verdict(review_id))

    print(
        json.dumps(
            {
                'reviewId': review_id,
                'sessionDir': str(session_dir),
                'changedFiles': changed_files,
                'status': 'initialized',
            },
            ensure_ascii=True,
            indent=2,
        ),
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
