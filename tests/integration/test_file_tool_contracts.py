import os
from pathlib import Path

import pytest

from createagents.infra.config import EnvironmentConfig
from tests.integration.test_file_tool_contracts_support import (
    assert_successful_file_read,
    create_file_read_challenge,
    file_tool_fixture_sandbox,
    fixture_path,
    make_file_read_prompt,
)


@pytest.mark.unit
class TestFileToolContracts:
    def test_fixture_path_uses_the_test_file_directory(self, tmp_path: Path):
        test_file = tmp_path / 'test_provider.py'

        result = fixture_path(str(test_file), 'sample.txt')

        assert result == tmp_path / 'fixtures' / 'sample.txt'

    def test_create_file_read_challenge_preserves_line_count_and_adds_proof(
        self, tmp_path: Path
    ):
        source_file = tmp_path / 'source' / 'sample.txt'
        source_file.parent.mkdir()
        source_file.write_text('First line\nFinal line\n', encoding='utf-8')

        challenge_file, proof_token = create_file_read_challenge(
            source_file,
            tmp_path / 'sandbox',
            proof_token='file-tool-proof-unit',
        )

        assert proof_token == 'file-tool-proof-unit'
        assert challenge_file == tmp_path / 'sandbox' / 'sample.txt'
        assert challenge_file.read_text(encoding='utf-8') == (
            'First line\nFinal line file-tool-proof-unit\n'
        )
        assert source_file.read_text(encoding='utf-8') == (
            'First line\nFinal line\n'
        )

    def test_create_file_read_challenge_rejects_empty_source(
        self, tmp_path: Path
    ):
        source_file = tmp_path / 'empty.txt'
        source_file.write_text('', encoding='utf-8')

        with pytest.raises(ValueError, match='at least one line'):
            create_file_read_challenge(source_file, tmp_path / 'sandbox')

    def test_file_tool_fixture_sandbox_restores_environment_and_cache(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ):
        previous_directory = tmp_path / 'previous'
        fixture_file = tmp_path / 'fixture' / 'sample.txt'
        fixture_file.parent.mkdir()
        fixture_file.write_text('fixture', encoding='utf-8')
        monkeypatch.setenv('FILE_TOOL_BASE_DIR', str(previous_directory))
        EnvironmentConfig.clear_cache()

        try:
            assert EnvironmentConfig.get_env('FILE_TOOL_BASE_DIR') == str(
                previous_directory
            )

            with file_tool_fixture_sandbox(monkeypatch, fixture_file):
                assert os.getenv('FILE_TOOL_BASE_DIR') == str(
                    fixture_file.parent
                )
                assert EnvironmentConfig.get_env('FILE_TOOL_BASE_DIR') == str(
                    fixture_file.parent
                )

            assert os.getenv('FILE_TOOL_BASE_DIR') == str(previous_directory)
            assert EnvironmentConfig.get_env('FILE_TOOL_BASE_DIR') == str(
                previous_directory
            )
        finally:
            EnvironmentConfig.clear_cache()

    def test_successful_file_read_requires_facts_and_invocation_proof(self):
        response = (
            'The file has 4 lines. Alice appears in it. file-tool-proof-unit'
        )
        result = assert_successful_file_read(
            response,
            {'4', 'Alice'},
            'file-tool-proof-unit',
        )

        assert result == response

    @pytest.mark.parametrize(
        'response',
        [
            'Could not read the file, but it has 4 lines. proof-token',
            'Unable to access the file with 4 lines. proof-token',
            'File not found; expected 4 lines. proof-token',
        ],
    )
    def test_successful_file_read_rejects_provider_failure_messages(
        self, response: str
    ):
        with pytest.raises(AssertionError, match='file read failure'):
            assert_successful_file_read(response, {'4'}, 'proof-token')

    def test_successful_file_read_rejects_embedded_numeric_fact(self):
        with pytest.raises(AssertionError, match='numeric fact'):
            assert_successful_file_read(
                'The file has 14 lines. proof-token',
                {'4'},
                'proof-token',
            )

    def test_successful_file_read_rejects_missing_invocation_proof(self):
        with pytest.raises(AssertionError, match='invocation proof'):
            assert_successful_file_read(
                'The file has 4 lines.',
                {'4'},
                'proof-token',
            )

    def test_make_file_read_prompt_includes_path_question_and_token_rule(
        self, tmp_path: Path
    ):
        file_path = tmp_path / 'sample.txt'
        question = 'Return the line count as an Arabic numeral.'

        prompt = make_file_read_prompt(file_path, question)

        assert str(file_path) in prompt
        assert question in prompt
        assert 'file-tool-proof-' in prompt
        assert 'readlocalfile' in prompt
