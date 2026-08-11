import re

import pytest

from createagents.presentation.cli.ui import MarkdownTerminalFormatter
from createagents.utils import TextSanitizer


@pytest.mark.unit
class TestWrapText:
    def test_wrap_empty_text(self):
        result = MarkdownTerminalFormatter._wrap_text('', 80)
        assert result == []

    def test_wrap_single_word_fits(self):
        result = MarkdownTerminalFormatter._wrap_text('Hello', 80)
        assert result == ['Hello']

    def test_wrap_single_word_exceeds_width(self):
        result = MarkdownTerminalFormatter._wrap_text(
            'Supercalifragilisticexpialidocious', 10
        )
        assert result == ['Supercalifragilisticexpialidocious']

    def test_wrap_multiple_words_fits(self):
        result = MarkdownTerminalFormatter._wrap_text('Hello World', 80)
        assert result == ['Hello World']

    def test_wrap_multiple_words_needs_wrapping(self):
        text = 'The quick brown fox jumps over the lazy dog'
        result = MarkdownTerminalFormatter._wrap_text(text, 20)

        all_words = ' '.join(result).split()
        original_words = text.split()
        assert set(all_words) == set(original_words)

        for line in result:
            assert len(line) <= 20

    def test_wrap_with_width_zero(self):
        result = MarkdownTerminalFormatter._wrap_text('Hello World', 0)
        assert len(result) > 0

    def test_wrap_with_width_one(self):
        result = MarkdownTerminalFormatter._wrap_text('Hello World', 1)
        assert len(result) >= 2

    def test_wrap_preserves_word_order(self):
        text = 'One Two Three Four Five Six Seven Eight'
        result = MarkdownTerminalFormatter._wrap_text(text, 15)

        reconstructed = ' '.join(result)
        words_original = text.split()
        words_wrapped = reconstructed.split()

        assert words_original == words_wrapped

    def test_wrap_with_extra_spaces(self):
        text = 'Hello    World    Test'
        result = MarkdownTerminalFormatter._wrap_text(text, 80)

        assert 'Hello' in result[0]
        assert 'World' in result[0]

    def test_wrap_very_long_text(self):
        text = ' '.join(['word'] * 100)
        result = MarkdownTerminalFormatter._wrap_text(text, 20)

        assert len(result) > 1
        for line in result:
            assert len(line) <= 20

    def test_wrap_single_long_word_with_small_width(self):
        result = MarkdownTerminalFormatter._wrap_text(
            'Antidisestablishmentarianism', 5
        )
        assert 'Antidisestablishmentarianism' in result

    def test_wrap_respects_width_boundary(self):
        text = 'Short text to wrap with specific width limit'
        width = 25
        result = MarkdownTerminalFormatter._wrap_text(text, width)

        for line in result:
            assert len(line) <= width

    def test_wrap_only_whitespace(self):
        result = MarkdownTerminalFormatter._wrap_text('     ', 80)
        assert result == []

    def test_wrap_text_with_tabs(self):
        text = 'Hello\tWorld\tTest'
        result = MarkdownTerminalFormatter._wrap_text(text, 80)

        assert len(result) > 0
        reconstructed = ' '.join(result)
        assert 'Hello' in reconstructed
        assert 'World' in reconstructed
        assert 'Test' in reconstructed

    def test_wrap_text_with_newlines_treated_as_spaces(self):
        text = 'Hello\nWorld\nTest'
        result = MarkdownTerminalFormatter._wrap_text(text, 80)

        assert len(result) > 0
        reconstructed = ' '.join(result)
        assert 'Hello' in reconstructed
        assert 'World' in reconstructed
        assert 'Test' in reconstructed

    def test_wrap_with_increasingly_larger_width(self):
        text = 'The quick brown fox jumps over the lazy dog'

        result_10 = MarkdownTerminalFormatter._wrap_text(text, 10)
        result_20 = MarkdownTerminalFormatter._wrap_text(text, 20)
        result_100 = MarkdownTerminalFormatter._wrap_text(text, 100)

        assert len(result_100) <= len(result_20) <= len(result_10)

    def test_wrap_consecutive_long_words(self):
        text = (
            'Supercalifragilisticexpialidocious Antidisestablishmentarianism'
        )
        result = MarkdownTerminalFormatter._wrap_text(text, 40)

        assert len(result) >= 1
        for line in result:
            assert len(line) <= 40


@pytest.mark.unit
class TestSanitize:
    def test_sanitize_normal_text(self):
        text = 'Hello World'
        result = TextSanitizer.sanitize(text)
        assert result == 'Hello World'

    def test_sanitize_empty_string(self):
        result = TextSanitizer.sanitize('')
        assert result == ''

    def test_sanitize_non_string_input(self):
        assert TextSanitizer.sanitize(123) == 123
        assert TextSanitizer.sanitize(None) is None
        assert TextSanitizer.sanitize([]) == []

    def test_sanitize_narrow_nbsp(self):
        text = 'Hello\u202fWorld'
        result = TextSanitizer.sanitize(text)
        assert '\u202f' not in result
        assert result == 'Hello World'

    def test_sanitize_nbsp(self):
        text = 'Hello\u00a0World'
        result = TextSanitizer.sanitize(text)
        assert '\u00a0' not in result
        assert result == 'Hello World'

    def test_sanitize_non_breaking_hyphen(self):
        text = 'Mother\u2011in\u2011law'
        result = TextSanitizer.sanitize(text)
        assert '\u2011' not in result
        assert result == 'Mother-in-law'

    def test_sanitize_thin_space(self):
        text = 'Hello\u2009World'
        result = TextSanitizer.sanitize(text)
        assert '\u2009' not in result
        assert result == 'Hello World'

    def test_sanitize_zero_width_space(self):
        text = 'Hello\u200bWorld'
        result = TextSanitizer.sanitize(text)
        assert '\u200b' not in result
        assert result == 'HelloWorld'

    def test_sanitize_zero_width_non_joiner(self):
        text = 'Hello\u200cWorld'
        result = TextSanitizer.sanitize(text)
        assert '\u200c' not in result
        assert result == 'HelloWorld'

    def test_sanitize_zero_width_joiner(self):
        text = 'Hello\u200dWorld'
        result = TextSanitizer.sanitize(text)
        assert '\u200d' not in result
        assert result == 'HelloWorld'

    def test_sanitize_multiple_problematic_chars(self):
        text = 'Hello\u202fWorld\u00a0Test\u200bString'
        result = TextSanitizer.sanitize(text)

        assert '\u202f' not in result
        assert '\u00a0' not in result
        assert '\u200b' not in result
        assert 'Hello World' in result
        assert 'Test' in result

    def test_sanitize_unicode_normalization(self):
        text = 'café'
        result = TextSanitizer.sanitize(text)

        assert result == 'café'

    def test_sanitize_special_unicode_characters_preserved(self):
        text = '你好 🎉 Привет'
        result = TextSanitizer.sanitize(text)

        assert '你好' in result
        assert '🎉' in result
        assert 'Привет' in result

    def test_sanitize_accented_characters(self):
        text = 'café naïve résumé'
        result = TextSanitizer.sanitize(text)

        assert 'café' in result
        assert 'naïve' in result
        assert 'résumé' in result

    def test_sanitize_idempotent(self):
        text = 'Hello\u202fWorld'
        once = TextSanitizer.sanitize(text)
        twice = TextSanitizer.sanitize(once)

        assert once == twice

    def test_sanitize_with_newlines_preserved(self):
        text = 'Line1\nLine2\nLine3'
        result = TextSanitizer.sanitize(text)

        assert result == text
        assert '\n' in result

    def test_sanitize_with_tabs_preserved(self):
        text = 'Col1\tCol2\tCol3'
        result = TextSanitizer.sanitize(text)

        assert result == text
        assert '\t' in result

    def test_sanitize_mixed_spaces(self):
        text = 'A\u202fB\u00a0C\u2009D E'
        result = TextSanitizer.sanitize(text)

        assert ' ' in result
        assert '\u202f' not in result
        assert '\u00a0' not in result
        assert '\u2009' not in result


@pytest.mark.unit
class TestFormatMarkdownForTerminal:
    def test_format_non_string_input(self):
        assert MarkdownTerminalFormatter.format(123) == 123
        assert MarkdownTerminalFormatter.format(None) is None

    def test_format_empty_string(self):
        result = MarkdownTerminalFormatter.format('')
        assert result == ''

    def test_format_plain_text(self):
        text = 'This is plain text'
        result = MarkdownTerminalFormatter.format(text)

        assert 'This is plain text' in result

    def test_format_remove_br_tags(self):
        text = 'Line 1<br>Line 2<br/>Line 3'
        result = MarkdownTerminalFormatter.format(text)

        assert '<br' not in result
        assert '\n' in result

    def test_format_remove_html_tags(self):
        text = 'This is <b>bold</b> and <i>italic</i> and <span>span</span>'
        result = MarkdownTerminalFormatter.format(text)

        assert '<b>' not in result
        assert '<i>' not in result
        assert '<span>' not in result
        assert 'bold' in result
        assert 'italic' in result

    def test_format_remove_complex_html_tags(self):
        text = 'This is a <a href="link">link</a> and <div class="box">content</div>'
        result = MarkdownTerminalFormatter.format(text)

        assert '<a' not in result
        assert '<div' not in result
        assert 'link' in result
        assert 'content' in result

    def test_format_h1_header(self):
        text = '# Main Title'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Main Title' in result
        assert '───────' in result

    def test_format_h2_header(self):
        text = '## Section Title'
        result = MarkdownTerminalFormatter.format(text)
        assert 'Section Title' in result

    def test_format_h3_header(self):
        text = '### Subsection'
        result = MarkdownTerminalFormatter.format(text)
        assert 'Subsection' in result

    def test_format_h4_header_uses_indicator(self):
        result = MarkdownTerminalFormatter.format('#### Header')

        assert 'Header' in result
        assert '▌' in result

    def test_format_h5_h6_headers_render_text(self):
        for level in [5, 6]:
            markdown = '#' * level + ' Header'
            result = MarkdownTerminalFormatter.format(markdown)
            assert 'Header' in result

    def test_format_multiple_headers(self):
        text = '# Title\n## Section 1\n### Subsection\n## Section 2'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Title' in result
        assert 'Section 1' in result
        assert 'Subsection' in result
        assert 'Section 2' in result

    def test_format_bold_double_asterisk(self):
        text = 'This is **bold** text'
        result = MarkdownTerminalFormatter.format(text)

        assert '**' not in result
        assert 'bold' in result

    def test_format_bold_double_underscore(self):
        text = 'This is __bold__ text'
        result = MarkdownTerminalFormatter.format(text)

        assert '__' not in result
        assert 'bold' in result

    def test_format_italic_single_asterisk(self):
        text = 'This is *italic* text'
        result = MarkdownTerminalFormatter.format(text)

        assert '*italic*' not in result
        assert 'italic' in result

    def test_format_italic_single_underscore(self):
        text = 'This is _italic_ text'
        result = MarkdownTerminalFormatter.format(text)

        assert '_italic_' not in result
        assert 'italic' in result

    def test_format_mixed_bold_italic(self):
        text = 'This is **bold** and *italic* and __bold__ and _italic_'
        result = MarkdownTerminalFormatter.format(text)

        assert '**' not in result
        assert '__' not in result
        assert 'bold' in result
        assert 'italic' in result

    def test_format_unordered_list_dash(self):
        text = '- Item 1\n- Item 2\n- Item 3'
        result = MarkdownTerminalFormatter.format(text)

        assert '•' in result
        assert 'Item 1' in result
        assert 'Item 2' in result
        assert 'Item 3' in result

    def test_format_unordered_list_asterisk(self):
        text = '* Item 1\n* Item 2\n* Item 3'
        result = MarkdownTerminalFormatter.format(text)

        assert '•' in result
        assert 'Item 1' in result

    def test_format_unordered_list_plus(self):
        text = '+ Item 1\n+ Item 2\n+ Item 3'
        result = MarkdownTerminalFormatter.format(text)

        assert '•' in result
        assert 'Item 1' in result

    def test_format_ordered_list(self):
        text = '1. First\n2. Second\n3. Third'
        result = MarkdownTerminalFormatter.format(text)

        assert '→' in result
        assert 'First' in result
        assert 'Second' in result
        assert 'Third' in result

    def test_format_nested_list(self):
        text = '- Item 1\n  - Subitem 1.1\n  - Subitem 1.2\n- Item 2'
        result = MarkdownTerminalFormatter.format(text)

        assert '•' in result
        assert 'Item 1' in result
        assert 'Subitem' in result

    def test_format_horizontal_rule_dashes(self):
        text = 'Before\n---\nAfter'
        result = MarkdownTerminalFormatter.format(text)

        assert '─' in result
        assert 'Before' in result
        assert 'After' in result

    def test_format_horizontal_rule_asterisks(self):
        text = 'Before\n***\nAfter'
        result = MarkdownTerminalFormatter.format(text)

        assert '─' in result

    def test_format_horizontal_rule_underscores(self):
        text = 'Before\n___\nAfter'
        result = MarkdownTerminalFormatter.format(text)

        assert '─' in result

    def test_format_simple_table_two_columns(self):
        text = '| Header1 | Header2 |\n|---------|----------|\n| Value1  | Value2  |'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Header1' in result
        assert 'Value1' in result
        assert '│' in result or '▪' in result

    def test_format_table_with_long_content(self):
        text = '| Name | Description |\n|------|-------------|\n| Item | This is a very long description that should be wrapped properly in the terminal |'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Name' in result or 'Item' in result
        assert 'Description' in result or 'description' in result

    def test_format_multicolumn_table(self):
        text = '| Col1 | Col2 | Col3 |\n|------|------|------|\n| A | B | C |'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Col1' in result
        assert 'A' in result or '│' in result

    def test_format_consecutive_blank_lines(self):
        text = 'Line 1\n\n\n\nLine 2'
        result = MarkdownTerminalFormatter.format(text)

        assert '\n\n\n' not in result

    def test_format_trailing_spaces_removed(self):
        text = 'Line 1   \nLine 2   '
        result = MarkdownTerminalFormatter.format(text)

        lines = result.split('\n')
        for line in lines:
            assert not line.endswith(' ')

    def test_format_code_block_with_backticks(self):
        text = '`code` and ``double`` and ```\nblock\n```'
        result = MarkdownTerminalFormatter.format(text)

        assert 'code' in result

    def test_format_links_removed(self):
        text = '[Link text](https://example.com)'
        result = MarkdownTerminalFormatter.format(text)

        assert '[' not in result or 'Link text' in result

    def test_format_unicode_characters_preserved(self):
        text = 'Hello 你好 🎉 Привет'
        result = MarkdownTerminalFormatter.format(text)

        assert '你好' in result
        assert '🎉' in result
        assert 'Привет' in result

    def test_format_mixed_markdown(self):
        text = """# Main Title

## Section 1
This is *italic* and **bold** text.

- Bullet 1
- Bullet 2

1. Numbered 1
2. Numbered 2

---

| Header | Value |
|--------|-------|
| Row1   | Data1 |
"""
        result = MarkdownTerminalFormatter.format(text)

        assert 'Main Title' in result
        assert 'Section 1' in result
        assert '•' in result
        assert '→' in result
        assert '─' in result

    def test_format_empty_table_cells(self):
        text = '| Col1 | Col2 |\n|------|------|\n| | Empty |'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Col1' in result
        assert 'Empty' in result

    def test_format_list_with_complex_items(self):
        text = '- Item with **bold** and *italic*\n- Another **item**'
        result = MarkdownTerminalFormatter.format(text)

        assert '•' in result
        assert 'bold' in result
        assert 'italic' in result

    def test_format_header_with_markdown_inside(self):
        text = '# Header with **bold** and *italic*'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Header with' in result
        assert 'bold' in result

    def test_format_very_long_line(self):
        long_text = 'This is a very long line ' * 20
        result = MarkdownTerminalFormatter.format(long_text)

        assert 'This is a very long line' in result

    def test_format_special_markdown_chars_in_plain_text(self):
        text = 'Price is $5.99 * 2 = $11.98'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Price' in result

    def test_format_malformed_markdown(self):
        text = '**unclosed bold\n*unclosed italic\n- Incomplete list item: '
        result = MarkdownTerminalFormatter.format(text)

        assert isinstance(result, str)

    def test_format_preserves_paragraph_structure(self):
        text = 'Paragraph 1\n\nParagraph 2\n\nParagraph 3'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Paragraph 1' in result
        assert 'Paragraph 2' in result
        assert 'Paragraph 3' in result


@pytest.mark.unit
class TestTextSanitizerIntegration:
    def test_full_pipeline_sanitize_then_format(self):
        text = '# Title\u202f(with problematic char)\n\n**Bold** and *italic*'

        sanitized = TextSanitizer.sanitize(text)
        formatted = MarkdownTerminalFormatter.format(sanitized)

        assert 'Title' in formatted
        assert 'problematic char' in formatted
        assert '\u202f' not in formatted

    def test_format_already_formats_sanitization(self):
        text = '# Title\u202fTest\n**Bold**'

        result = MarkdownTerminalFormatter.format(text)

        assert '\u202f' not in result
        assert 'Title' in result
        assert 'Test' in result

    def test_markdown_with_unicode_content(self):
        text = '# 你好世界\n\n**中文** 和 *日本語*\n\n- 项目1\n- 項目2'

        result = MarkdownTerminalFormatter.format(text)

        assert '你好世界' in result
        assert '中文' in result
        assert '•' in result

    def test_complex_document_formatting(self):
        document = """# Project Documentation

## Overview
This is a **critical** project with *important* details.

### Features
- Feature 1: *Essential*
- Feature 2: **Must have**
- Feature 3: Optional

## Usage

| Command | Description |
|---------|-------------|
| start | **Starts** the service |
| stop | Stops the *running* service |

---

### Notes
- Created: 2024-01-01
- Modified: 2024-11-07
"""

        result = MarkdownTerminalFormatter.format(document)

        assert 'Project Documentation' in result
        assert 'Overview' in result
        assert 'Features' in result
        assert 'Usage' in result
        assert 'Command' in result
        assert '•' in result
        assert '─' in result or '━' in result

    def test_wrap_text_after_formatting(self):
        markdown = '# Title\n\nThis is a long line that might need wrapping when displayed in a terminal with limited width'

        formatted = MarkdownTerminalFormatter.format(markdown)
        wrapped = MarkdownTerminalFormatter._wrap_text(formatted, 40)

        assert len(wrapped) > 0
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        for line in wrapped:
            cleaned = ansi_escape.sub('', line)
            if cleaned.strip('─') == '':
                continue
            assert len(cleaned) <= 40


@pytest.mark.unit
class TestEdgeCasesAndErrorHandling:
    def test_extremely_large_text(self):
        large_text = 'word ' * 10000

        result_wrapped = MarkdownTerminalFormatter._wrap_text(large_text, 80)
        assert len(result_wrapped) > 0

        result_sanitized = TextSanitizer.sanitize(large_text)
        assert 'word' in result_sanitized

        result_formatted = MarkdownTerminalFormatter.format(large_text)
        assert 'word' in result_formatted

    def test_none_handling(self):
        assert TextSanitizer.sanitize(None) is None
        assert MarkdownTerminalFormatter.format(None) is None

    def test_numeric_input_handling(self):
        assert TextSanitizer.sanitize(42) == 42
        assert MarkdownTerminalFormatter.format(3.14) == 3.14

    def test_list_input_handling(self):
        lst = [1, 2, 3]
        assert TextSanitizer.sanitize(lst) == lst
        assert MarkdownTerminalFormatter.format(lst) == lst

    def test_unicode_edge_cases(self):
        test_cases = [
            '\u200b\u200c\u200d',
            '\u202f\u00a0\u2009',
            '🏴',
            '\uffff',
        ]

        for text in test_cases:
            result = TextSanitizer.sanitize(text)
            assert isinstance(result, str)

    def test_mixed_line_endings(self):
        text = 'Line1\nLine2\r\nLine3\rLine4'
        result = MarkdownTerminalFormatter.format(text)

        assert 'Line' in result

    def test_format_with_only_markdown_syntax(self):
        text = '# ## ### #### ##### ######'
        result = MarkdownTerminalFormatter.format(text)

        assert isinstance(result, str)

    def test_wrap_text_width_larger_than_content(self):
        text = 'Short'
        result = MarkdownTerminalFormatter._wrap_text(text, 1000)

        assert result == ['Short']

    def test_consecutive_formatting_calls(self):
        text = '# Test\n**bold** and *italic*'

        result1 = MarkdownTerminalFormatter.format(text)
        result2 = MarkdownTerminalFormatter.format(result1)
        result3 = MarkdownTerminalFormatter.format(result2)

        assert result2 == result3
