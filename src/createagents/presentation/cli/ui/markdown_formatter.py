import re

from ....utils.text_sanitizer import TextSanitizer
from .color_scheme import ColorScheme


class MarkdownTerminalFormatter:
    """Renders Markdown as ANSI-styled text for the interactive CLI.

    This is terminal presentation logic: it depends on `ColorScheme` and
    therefore belongs to the presentation layer, not to `utils`.
    """

    @staticmethod
    def format(text: str) -> str:
        """Format Markdown text for better readability in the terminal.

        Convert Markdown elements into styled terminal text with ANSI codes.
        """
        if not isinstance(text, str):
            return text

        # First, sanitize problematic unicode characters
        text = TextSanitizer.sanitize(text)

        # Remove HTML <br> tags and replace with newlines
        text = re.sub(r'<br\s*/?>\s*', '\n', text, flags=re.IGNORECASE)

        # Remove other common HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Convert headers with colors and better formatting
        text = re.sub(
            r'^######\s+(.+)$',
            rf'{ColorScheme.CYAN}{ColorScheme.BOLD}\1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^#####\s+(.+)$',
            rf'{ColorScheme.CYAN}{ColorScheme.BOLD}\1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^####\s+(.+)$',
            rf'{ColorScheme.PURPLE}{ColorScheme.BOLD}▌\1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^###\s+(.+)$',
            rf'{ColorScheme.PURPLE}{ColorScheme.BOLD}▌\1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^##\s+(.+)$',
            rf'\n{ColorScheme.BLUE}{ColorScheme.BOLD}▐ \1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^#\s+(.+)$',
            rf'\n{ColorScheme.BLUE}{ColorScheme.BOLD}▐ \1{ColorScheme.RESET}\n{ColorScheme.DARK_GRAY}{"─" * 50}{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )

        # Convert bold formatting (**text** or __text__) to ANSI bold
        text = re.sub(
            r'\*\*(.+?)\*\*', rf'{ColorScheme.BOLD}\1{ColorScheme.RESET}', text
        )
        text = re.sub(
            r'__(.+?)__', rf'{ColorScheme.BOLD}\1{ColorScheme.RESET}', text
        )

        # Convert italic formatting (*text* or _text_) to ANSI italic
        text = re.sub(
            r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)',
            rf'{ColorScheme.ITALIC}\1{ColorScheme.RESET}',
            text,
        )
        text = re.sub(
            r'(?<!_)_(?!_)(.+?)_(?!_)',
            rf'{ColorScheme.ITALIC}\1{ColorScheme.RESET}',
            text,
        )

        # Convert unordered lists with colored bullets
        text = re.sub(
            r'^(\s*)[-*+]\s+',
            rf'\1{ColorScheme.GREEN}•{ColorScheme.RESET} ',
            text,
            flags=re.MULTILINE,
        )

        # Convert ordered lists with colored arrows
        text = re.sub(
            r'^(\s*)\d+\.\s+',
            rf'\1{ColorScheme.BLUE}→{ColorScheme.RESET} ',
            text,
            flags=re.MULTILINE,
        )

        # Convert markdown horizontal rules to styled separators
        text = re.sub(
            r'^[\-\*_]{3,}\s*$',
            rf'{ColorScheme.DARK_GRAY}{"─" * 60}{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )

        # Convert simple tables (just remove pipes and adjust)
        # Detect table lines (|...|...|)
        lines = text.split('\n')
        formatted_lines = []
        in_table = False
        max_line_width = 70

        for line in lines:
            # Detect if this is a table line
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    formatted_lines.append(
                        f'\n{ColorScheme.DARK_GRAY}{"─" * max_line_width}{ColorScheme.RESET}'
                    )

                # Remove pipes and format cells
                cells = [cell.strip() for cell in line.split('|')]
                cells = [cell for cell in cells if cell]  # Remove empty cells

                # Check if it's a separator line (|---|---|)
                if all(re.match(r'^[\-:]+$', cell) for cell in cells):
                    continue  # Skip separator lines

                # Format table row with better readability
                if len(cells) == 2:
                    # Two-column table: format as label-value pairs
                    label, value = cells[0], cells[1]
                    formatted_lines.append(
                        f'  {ColorScheme.CYAN}▪{ColorScheme.RESET} '
                        f'{ColorScheme.BOLD}{label}{ColorScheme.RESET}'
                    )

                    # Wrap long values to fit terminal width
                    if len(value) > max_line_width - 6:
                        wrapped_lines = MarkdownTerminalFormatter._wrap_text(
                            value, max_line_width - 6
                        )
                        formatted_lines.extend(
                            f'    {wrapped_line}'
                            for wrapped_line in wrapped_lines
                        )
                    else:
                        formatted_lines.append(f'    {value}')
                    formatted_lines.append('')  # Add blank line between rows
                else:
                    # Multi-column table: join with separators
                    formatted_line = (
                        f' {ColorScheme.DARK_GRAY}│{ColorScheme.RESET} '.join(
                            str(cell) for cell in cells
                        )
                    )
                    formatted_lines.append(f'  {formatted_line}')
            else:
                if in_table:
                    formatted_lines.append(
                        f'{ColorScheme.DARK_GRAY}{"─" * max_line_width}{ColorScheme.RESET}\n'
                    )
                    in_table = False
                formatted_lines.append(line)

        if in_table:
            formatted_lines.append(
                f'{ColorScheme.DARK_GRAY}{"─" * max_line_width}{ColorScheme.RESET}'
            )

        text = '\n'.join(formatted_lines)

        # Remove consecutive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove trailing spaces on lines
        return re.sub(r' +$', '', text, flags=re.MULTILINE)

    @staticmethod
    def _wrap_text(text: str, width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current_line: list[str] = []
        current_length = 0

        for word in words:
            word_length = len(word)
            if current_length + word_length + len(current_line) > width:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    lines.append(word)
                    current_length = 0
            else:
                current_line.append(word)
                current_length += word_length

        if current_line:
            lines.append(' '.join(current_line))

        return lines
