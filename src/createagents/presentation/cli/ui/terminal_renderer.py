import sys
from collections.abc import AsyncIterator
from datetime import datetime

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .color_scheme import ColorScheme
from .terminal_formatter import TerminalFormatter


class TerminalRenderer:
    """Handles rendering of visual components to the terminal.

    Responsibility: Render UI components to the terminal.
    This follows SRP by focusing solely on rendering operations.
    """

    def __init__(self, show_timestamps: bool = False) -> None:
        """Initialize the terminal renderer.

        Args:
            show_timestamps: Whether to display timestamps in messages.
        """
        self._formatter = TerminalFormatter()
        self._show_timestamps = show_timestamps
        self._console = Console()

    def _get_timestamp(self) -> str:
        """Get formatted timestamp for messages.

        Returns:
            Formatted timestamp string or empty if disabled.
        """
        if not self._show_timestamps:
            return ''
        now = datetime.now().astimezone()
        return f'{ColorScheme.get_timestamp_color()}{now.strftime("%H:%M")}{ColorScheme.RESET} '

    def render_welcome_screen(self) -> None:
        """Render the welcome screen with modern ASCII banner."""
        self.clear_screen()

        # Modern, minimal ASCII banner
        banner = f"""{ColorScheme.PURPLE}{ColorScheme.BOLD}
    ╔═══════════════════════════════════════╗
    ║     🤖  AI CHAT SYSTEM  ✨           ║
    ║     Enterprise Agent Framework        ║
    ╚═══════════════════════════════════════╝{ColorScheme.RESET}
"""
        print(banner)

        # Welcome message with icons
        print(
            f'{ColorScheme.GREEN}●{ColorScheme.RESET} '
            f'{ColorScheme.BOLD}System Ready{ColorScheme.RESET} '
            f'{ColorScheme.GRAY}• Type your message to begin{ColorScheme.RESET}'
        )

        # Commands help with better formatting
        print(
            f'\n{ColorScheme.DARK_GRAY}┌─ Available Commands{ColorScheme.RESET}\n'
            f'{ColorScheme.DARK_GRAY}│{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/help{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/metrics{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/configs{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/tools{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/clear{ColorScheme.RESET} '
            f'{ColorScheme.GRAY}exit{ColorScheme.RESET}\n'
            f'{ColorScheme.DARK_GRAY}└{"─" * 45}{ColorScheme.RESET}\n'
        )

    def render_message_box(
        self, message: str, color: str, align: str = 'left', icon: str = ''
    ) -> None:
        """Render a message inside a rounded box.

        Args:
            message: The message to display.
            color: ANSI color code for the box.
            align: Alignment ('left' or 'right').
            icon: Optional icon to display before message.
        """
        timestamp = self._get_timestamp()
        # Not named `box`: that is the `rich` module imported above.
        rendered = self._formatter.format_rounded_box(
            message, color, align, icon, timestamp
        )
        print(rendered)

    def render_user_message(self, message: str) -> None:
        """Render a user message (right-aligned, blue).

        Args:
            message: The user's message.
        """
        self.render_message_box(
            message, ColorScheme.get_user_color(), align='right', icon='👤'
        )

    def render_ai_message(self, message: str) -> None:
        """Render an AI message (left-aligned, purple).

        Args:
            message: The AI's message.
        """
        self.render_message_box(
            message, ColorScheme.get_ai_color(), align='left', icon='🤖'
        )

    async def render_ai_message_streaming(
        self, token_generator: AsyncIterator[str]
    ) -> None:
        """Render AI tokens in real time inside a purple panel.

        The panel only appears once the first token arrives, so the
        "AI is thinking..." indicator stays visible until then.

        Args:
            token_generator: Async iterator yielding response tokens.
        """
        first_token = await anext(aiter(token_generator), None)
        if first_token is None:
            self.clear_thinking_indicator()
            return

        self.clear_thinking_indicator()

        full_response = first_token
        with Live(
            self.__build_panel(full_response),
            console=self._console,
            refresh_per_second=20,
        ) as live:
            async for token in token_generator:
                full_response += token
                live.update(self.__build_panel(full_response))

    @staticmethod
    def __build_panel(text: str) -> Panel:
        """Wrap streamed text in the rounded panel used for AI replies."""
        return Panel(
            Text(text),
            style='bold purple',
            box=box.ROUNDED,
            padding=(0, 1),
            expand=False,
        )

    def render_system_message(self, message: str) -> None:
        """Render a system message (left-aligned, cyan).

        Args:
            message: The system message.
        """
        self.render_message_box(
            message,
            ColorScheme.get_system_color(),
            align='left',
            icon='\N{INFORMATION SOURCE}\ufe0f',
        )

    def render_success_message(self, message: str) -> None:
        """Render a success message (left-aligned, green).

        Args:
            message: The success message.
        """
        self.render_message_box(
            message, ColorScheme.get_success_color(), align='left', icon='✓'
        )

    def render_thinking_indicator(self) -> None:
        """Display 'AI is thinking...' indicator with animation effect."""
        print(
            f'{ColorScheme.DIM}{ColorScheme.PURPLE}'
            f'🤖 AI is thinking...{ColorScheme.RESET}',
            end='\r',
        )
        sys.stdout.flush()

    def clear_thinking_indicator(self) -> None:
        """Clear the thinking indicator line."""
        sys.stdout.write(ColorScheme.CLEAR_LINE)
        sys.stdout.flush()

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        print(ColorScheme.CLEAR_SCREEN, end='')
        sys.stdout.flush()

    def clear_input_lines(self, num_lines: int = 2) -> None:
        """Clear the specified number of lines above cursor.

        Args:
            num_lines: Number of lines to clear.
        """
        for _ in range(num_lines):
            sys.stdout.write(ColorScheme.MOVE_UP)
            sys.stdout.write(ColorScheme.CLEAR_LINE)
        sys.stdout.flush()

    def render_prompt(self, prompt: str = '💬 Your message') -> None:
        """Render the input prompt.

        Args:
            prompt: The prompt message to display.
        """
        print(f'{ColorScheme.GRAY}{prompt}{ColorScheme.RESET}')

    def render_input_indicator(self) -> None:
        """Render the input indicator with modern arrow."""
        print(
            f'{ColorScheme.BLUE}{ColorScheme.BOLD}▶ {ColorScheme.RESET}',
            end='',
        )

    def render_spacer(self) -> None:
        """Render a subtle separator line."""
        print(f'{ColorScheme.DARK_GRAY}{"─" * 50}{ColorScheme.RESET}')

    def render_goodbye(self) -> None:
        """Render goodbye message with icon."""
        print(
            f'\n{ColorScheme.PURPLE}👋 Goodbye! Thanks for using AI Chat System.{ColorScheme.RESET}'
        )

    def render_error(self, error_message: str) -> None:
        """Render an error message with icon and formatting.

        Args:
            error_message: The error message to display.
        """
        print(
            f'\n{ColorScheme.get_error_color()}{ColorScheme.BOLD}✗ Error:{ColorScheme.RESET} '
            f'{ColorScheme.get_error_color()}{error_message}{ColorScheme.RESET}'
        )

    def render_interrupt(self) -> None:
        """Render session interrupted message."""
        print(
            f'\n{ColorScheme.YELLOW}⚠ Session interrupted.{ColorScheme.RESET}'
        )
