import os
import re

import pytest

from createagents.presentation.cli.ui import terminal_formatter
from createagents.presentation.cli.ui.color_scheme import ColorScheme
from createagents.presentation.cli.ui.terminal_formatter import (
    TerminalFormatter,
)


@pytest.mark.unit
class TestTerminalFormatter:
    def test_terminal_formatter_scenarios_display_width_handles_wide_unicode(
        self,
    ):
        text = f'{ColorScheme.BLUE}A{ColorScheme.RESET}界'

        result = TerminalFormatter.get_display_width(text)

        assert result == 3

    def test_terminal_formatter_scenarios_wrap_text_applies_subsequent_indent(
        self,
    ):
        text = ' '.join(['word'] * 30)

        lines = TerminalFormatter.wrap_text(
            text,
            max_width=10,
            subsequent_indent='>>',
        )

        assert len(lines) > 2
        assert any(line.startswith('>>') for line in lines[1:])

    def test_terminal_formatter_scenarios_format_box_includes_icon_and_timestamp(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            TerminalFormatter,
            'get_terminal_width',
            staticmethod(lambda: 60),
        )
        monkeypatch.setattr(
            TerminalFormatter,
            'wrap_text',
            staticmethod(lambda text, max_width, subsequent_indent='': [text]),
        )

        box = TerminalFormatter.format_rounded_box(
            'Sample message',
            ColorScheme.BLUE,
            align='left',
            icon='👤',
            timestamp='[10:00]',
        )
        lines = box.splitlines()

        assert '👤' in lines[1]
        assert ColorScheme.BLUE in box
        assert lines[0].startswith('[10:00]')
        assert any(edge in box for edge in ('╭', '╯'))


def _strip_ansi(text: str) -> str:
    return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)


class _FakeShutil:
    """Stand-in for the `shutil` name bound inside terminal_formatter.

    Patching `shutil.get_terminal_size` itself would also hijack pytest's own
    terminal writer and crash the run, so only the module-level name is
    swapped.
    """

    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error

    def get_terminal_size(self, *args, **kwargs):
        if self._error is not None:
            raise self._error('no tty')
        return self._result


@pytest.mark.unit
class TestGetTerminalWidth:
    def test_returns_the_real_terminal_columns(self, monkeypatch):
        monkeypatch.setattr(
            terminal_formatter,
            'shutil',
            _FakeShutil(result=os.terminal_size((123, 40))),
        )

        assert TerminalFormatter.get_terminal_width() == 123

    @pytest.mark.parametrize('error', [OSError, ValueError])
    def test_falls_back_to_100_when_the_size_is_unavailable(
        self, monkeypatch, error
    ):
        monkeypatch.setattr(
            terminal_formatter, 'shutil', _FakeShutil(error=error)
        )

        assert TerminalFormatter.get_terminal_width() == 100


@pytest.mark.unit
class TestWrapText:
    def test_blank_text_wraps_to_a_single_empty_line(self):
        assert TerminalFormatter.wrap_text('   \t ', max_width=40) == ['']

    def test_width_below_the_floor_is_raised_to_40(self):
        text = 'x' * 60

        assert TerminalFormatter.wrap_text(text, max_width=5) == [
            'x' * 40,
            'x' * 20,
        ]


@pytest.mark.unit
class TestFormatRoundedBoxLayout:
    @staticmethod
    def _fixed_width(monkeypatch, width=60):
        monkeypatch.setattr(
            TerminalFormatter,
            'get_terminal_width',
            staticmethod(lambda: width),
        )

    def test_blank_lines_inside_the_text_are_preserved(self, monkeypatch):
        self._fixed_width(monkeypatch)

        box = TerminalFormatter.format_rounded_box(
            'first\n\nthird', ColorScheme.BLUE
        )
        content = box.splitlines()[1:-1]

        assert len(content) == 3
        assert 'first' in content[0]
        assert _strip_ansi(content[1]).strip('│ ') == ''
        assert 'third' in content[2]

    def test_bullet_lines_keep_their_indent_when_wrapped(self, monkeypatch):
        self._fixed_width(monkeypatch)
        bullet = '  • ' + ' '.join(['palavra'] * 20)

        box = TerminalFormatter.format_rounded_box(bullet, ColorScheme.BLUE)
        content = [line for line in box.splitlines() if 'palavra' in line]

        assert len(content) > 1
        # Continuation lines are indented to sit under the bullet text.
        second = content[1].split('│ ', 1)[1]
        assert second.startswith('    ')

    def test_right_alignment_indents_the_box(self, monkeypatch):
        self._fixed_width(monkeypatch, width=60)

        box = TerminalFormatter.format_rounded_box(
            'hi', ColorScheme.BLUE, align='right'
        )
        top = box.splitlines()[0]

        assert top.startswith(' ')
        assert len(top) - len(top.lstrip(' ')) == 60 - (2 + 2) - 2

    def test_right_aligned_timestamp_shifts_the_indent_left(self, monkeypatch):
        self._fixed_width(monkeypatch, width=60)
        timestamp = (
            f'{ColorScheme.get_timestamp_color()}[10:00]{ColorScheme.RESET}'
        )

        plain = TerminalFormatter.format_rounded_box(
            'hi', ColorScheme.BLUE, align='right'
        ).splitlines()[0]
        stamped = TerminalFormatter.format_rounded_box(
            'hi', ColorScheme.BLUE, align='right', timestamp=timestamp
        ).splitlines()[0]

        plain_indent = len(plain) - len(plain.lstrip(' '))
        stamped_indent = len(stamped) - len(stamped.lstrip(' '))

        # '[10:00]' is 7 visible chars, plus the one-space gap.
        assert stamped_indent == plain_indent - 8
        assert '[10:00]' in stamped
