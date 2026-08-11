import sys
from unittest.mock import Mock, patch

import pytest

from createagents.presentation.cli.ui.color_scheme import ColorScheme
from createagents.presentation.cli.ui.terminal_renderer import TerminalRenderer


@pytest.mark.unit
class TestTerminalRenderer:
    def test_terminal_renderer_scenarios_render_message_box_uses_formatter(
        self,
    ):
        renderer = TerminalRenderer()
        renderer._formatter = Mock()
        renderer._formatter.format_rounded_box.return_value = 'formatted'

        with patch('builtins.print') as mock_print:
            renderer.render_message_box(
                'message',
                ColorScheme.PURPLE,
                align='right',
                icon='X',
            )

        renderer._formatter.format_rounded_box.assert_called_once_with(
            'message',
            ColorScheme.PURPLE,
            'right',
            'X',
            '',
        )
        mock_print.assert_called_once_with('formatted')

    def test_terminal_renderer_scenarios_render_error_outputs_colored_message(
        self,
    ):
        renderer = TerminalRenderer()

        with patch('builtins.print') as mock_print:
            renderer.render_error('Failure detected')

        printed = mock_print.call_args[0][0]
        assert 'Failure detected' in printed
        assert '✗' in printed
        assert ColorScheme.get_error_color() in printed

    def test_terminal_renderer_scenarios_render_prompt_prints_gray_text(self):
        renderer = TerminalRenderer()

        with patch('builtins.print') as mock_print:
            renderer.render_prompt('Custom prompt')

        printed = mock_print.call_args[0][0]
        assert 'Custom prompt' in printed
        assert ColorScheme.GRAY in printed

    def test_terminal_renderer_scenarios_clear_input_lines_writes_control_sequences(
        self, monkeypatch
    ):
        renderer = TerminalRenderer()
        mock_stdout = Mock()
        monkeypatch.setattr(sys, 'stdout', mock_stdout)

        renderer.clear_input_lines(3)

        assert mock_stdout.write.call_count == 6
        mock_stdout.flush.assert_called_once()
