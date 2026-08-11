from unittest.mock import patch

import pytest

from createagents.presentation.cli.io.input_reader import InputReader


@pytest.mark.unit
def test_scenario_read_user_input_returns_value():
    reader = InputReader()

    with patch('builtins.input', return_value='hello') as mock_input:
        result = reader.read_user_input('> ')

    assert result == 'hello'
    mock_input.assert_called_once_with('> ')
