import pytest
from ..ui import *

def test_wrap_line():
    text = '    convert noun or verb to its essential characteristic / ~EN "-ish" / ~EN "-ful"'
    result = wrap_line_with_indent(text, 17)
    expected = '    convert noun\n    or verb to\n    its\n    essential\n    characteristi\n    c / ~EN\n    "-ish" / ~EN\n    "-ful"'
    assert result == expected

def test_wrap_block_with_indent_one_line():
    text = "This is a long line of text that needs to be wrapped. It should be split into multiple lines with the specified indentation."
    result = wrap_block_with_indent(text, 20)
    expected = "This is a long line\nof text that needs\nto be wrapped. It\nshould be split\ninto multiple lines\nwith the specified\nindentation."
    assert result == expected

def test_wrap_block_with_indent_short_line():
    text = "Short line"
    result = wrap_block_with_indent(text, 20)
    assert result == text

def test_wrap_block_with_indent_empty_string():
    result = wrap_block_with_indent("", 20)
    assert result == ""

def test_wrap_block_with_indent_multiline():
    text = "This is a long line of text that needs to be wrapped.\nThis is\nanother long line of text\nthat needs to be wrapped."
    result = wrap_block_with_indent(text, 20)
    expected = "This is a long line\nof text that needs\nto be wrapped.\nThis is\nanother long line\nof text\nthat needs to be\nwrapped."
    assert result == expected

def test_wrap_block_with_indent_multiline_indented():
    text = "    This is a long line of text that needs to be wrapped.\n    This is another long line of text that needs to be wrapped."
    result = wrap_block_with_indent(text, 20)
    expected = "    This is a long\n    line of text\n    that needs to\n    be wrapped.\n    This is another\n    long line of\n    text that needs\n    to be wrapped."
    assert result == expected