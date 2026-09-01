"""Shared observable contracts for real-provider file-tool tests."""

import re
from collections.abc import Collection, Generator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pytest

from createagents.infra.config import EnvironmentConfig

__test__ = False

_FILE_READ_FAILURE_INDICATORS = (
    'file not found',
    'access denied',
    'file read error',
    'file processing error',
    'permission denied',
    'could not read',
    'unable to read',
    'failed to read',
    'could not access',
    'unable to access',
    'failed to access',
    'erro de leitura',
    'acesso negado',
    'arquivo inexistente',
    'não foi possível ler',
    'não foi possível acessar',
)


def fixture_path(test_file: str, filename: str) -> Path:
    """Resolve an integration fixture independently from the working directory."""
    return Path(test_file).resolve().parent / 'fixtures' / filename


def create_file_read_challenge(
    source_file: Path,
    destination_dir: Path,
    proof_token: str | None = None,
) -> tuple[Path, str]:
    """Copy a text fixture with a per-run token that proves file access."""
    token = proof_token or f'file-tool-proof-{uuid4().hex}'
    lines = source_file.read_text(encoding='utf-8').splitlines()
    if not lines:
        raise ValueError(
            'The file-tool fixture must contain at least one line.'
        )

    challenge_file = destination_dir / source_file.name
    challenge_file.parent.mkdir(parents=True, exist_ok=True)
    lines[-1] = f'{lines[-1]} {token}'
    challenge_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return challenge_file, token


def make_file_read_prompt(
    file_path: Path | str,
    core_question: str,
) -> str:
    """Build an unambiguous prompt requiring file reading and the exact proof token.

    Args:
        file_path: Path to the target fixture file.
        core_question: Question asking for specific facts inside the file.

    Returns:
        A formatted user ask string for real-provider integration tests.
    """
    return (
        f'Read {file_path}. {core_question} '
        'Include verbatim the complete security token starting with '
        '"file-tool-proof-" found at the end of the file. '
        'Use the readlocalfile tool.'
    )


@contextmanager
def file_tool_fixture_sandbox(
    monkeypatch: pytest.MonkeyPatch,
    fixture_file: Path,
) -> Generator[None, None, None]:
    """Allow the file tool to access only the fixture directory for one test."""
    with monkeypatch.context() as sandbox_monkeypatch:
        sandbox_monkeypatch.setenv(
            'FILE_TOOL_BASE_DIR', str(fixture_file.parent)
        )
        EnvironmentConfig.clear_cache()
        try:
            yield
        finally:
            EnvironmentConfig.clear_cache()


def assert_successful_file_read(
    response: str,
    expected_facts: Collection[str],
    invocation_proof: str,
) -> str:
    """Verify provider output and return the validated response."""
    assert response.strip(), 'Provider returned an empty response.'
    response_folded = response.casefold()

    for fact in expected_facts:
        if fact.isdigit():
            assert re.search(rf'\b{re.escape(fact)}\b', response), (
                f'Expected numeric fact not found: {fact!r}'
            )
        else:
            assert fact.casefold() in response_folded, (
                f'Expected fact not found: {fact!r}'
            )

    assert invocation_proof.casefold() in response_folded, (
        'Provider response omitted the file-only invocation proof.'
    )

    assert not any(
        indicator in response_folded
        for indicator in _FILE_READ_FAILURE_INDICATORS
    ), 'Provider response indicates a file read failure.'
    return response
