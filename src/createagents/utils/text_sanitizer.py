import unicodedata


class TextSanitizer:
    """A utility class for sanitizing text.

    Provides layer-agnostic cleaning of problematic unicode characters.
    Terminal rendering lives in
    `presentation.cli.ui.markdown_formatter.MarkdownTerminalFormatter`.
    """

    @staticmethod
    def sanitize(text: str) -> str:
        """Remove problematic unicode characters and normalize the text.

        Args:
            text: The input text to be sanitized.

        Returns:
            The sanitized text with problematic characters removed or
            replaced, normalized to NFKC form. Non-string input is returned
            unchanged.
        """
        if not isinstance(text, str):
            return text

        # Remove specific problematic unicode characters
        problematic_chars = {
            '\u202f': ' ',  # Narrow no-break space → regular space
            '\u00a0': ' ',  # Non-breaking space → regular space
            '\u2011': '-',  # Non-breaking hyphen → regular hyphen '-'
            '\u2009': ' ',  # Thin space → regular space
            '\u200b': '',  # Zero-width space → remove
            '\u200c': '',  # Zero-width non-joiner → remove
            '\u200d': '',  # Zero-width joiner → remove
        }

        for char, replacement in problematic_chars.items():
            text = text.replace(char, replacement)

        # Normalize unicode to decomposed form (NFKC) for consistency
        return unicodedata.normalize('NFKC', text)
