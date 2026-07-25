import os
import time
from termcolor import cprint
if os.name == 'nt':
    import ctypes
    import struct
import sys

verbose = False

ERROR_COLOR = 'red'
WARNING_COLOR = 'yellow'
PROMPT_COLOR = 'cyan'
LEX_COLOR = 'yellow'
TAG_COLOR = 'red'
NOTE_COLOR = 'green'
EQUIV_COLOR = 'blue'
OPTION_COLOR = 'cyan'
CMD_COLOR = 'yellow'

def get_verbose():
    global verbose
    return verbose

def set_verbose(value):
    global verbose
    verbose = value

def _calc_terminal_size():
    if os.name == 'nt':
        h = ctypes.windll.kernel32.GetStdHandle(-12)  # STD_OUTPUT_HANDLE
        csbi = ctypes.create_string_buffer(22)
        res = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)

        if res:
            (bufx, bufy, curx, cury, wattr,
            left, top, right, bottom,
            maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
        else:
            sizex, sizey = 80, 25  # can't determine actual size - return default values

        return sizex, sizey
    else:
        rows, columns = os.popen('stty size', 'r').read().split()
        return int(columns), int(rows)

_last_termsize_check = 0
_last_sizex = None
_last_sizey = None
def get_terminal_size(force: bool = False):
    """
    Get the size of the terminal window.

    Args:
        force (bool): If True, force a recalculation of the terminal size.

    Returns:
        Tuple[int, int]: The width and height of the terminal window.
    """
    global _last_termsize_check, _last_sizex, _last_sizey
    now = time.time()
    if force or (now - _last_termsize_check > 10):
        _last_sizex, _last_sizey = _calc_terminal_size()
        _last_termsize_check = now
    return _last_sizex, _last_sizey
    
def wrap_line_with_indent(text: str, width: int=None, indent: str=None, first_width=None):
    """
    Wraps a single line of text to fit within the specified width,
    using either a specified indent string, or the indentation of
    the first line as a model.

    Args:
        text (str): The text to be wrapped.
        width (int): The maximum width of each line.
        indent (str): A string prefixed to each line after the first. If
            not given, the indent of the first line is used as a model.
        first_width (int): The width of the first line. This can model
            hanging indents or deeper indents on the first line, and can
            be helpful if the first line needs to end early because it
            is preceded by something not analyzed in the wrapping. If
            not specified, width is used for the first line as well. If
            this value is negative, first_width is subtracted from with,
            giving a relatively smaller first line.
    Returns:
        str: The wrapped text with indentation.
    """
    if width is None:
        width, _ = get_terminal_size()
    current_width = first_width if first_width else width
    if current_width < 0: current_width = width + current_width
    lines = []
    # Remove trailing spaces so they won't confuse our calculations.
    text = text.rstrip()
    if text:
        if indent is None:
            for i in range(len(text)):
                if text[i] != ' ':
                    break
            indent = ' ' * i if i > 0 else ''
        while len(text) > current_width:
            space_index = text.rfind(' ', len(indent) + 1, current_width)
            if space_index == -1:
                # If no space found within width, just split at width
                lines.append(text[:current_width])
                text = indent + text[current_width:]
            else:
                lines.append(text[:space_index].rstrip())
                text = indent + text[space_index + 1:]
            # If we were using a different width for the first line,
            # switch to the width for all remaining lines.
            current_width = width
        lines.append(text)
    return '\n'.join(lines)

def wrap_block_with_indent(text: str, width: int=None):
    """
    Wrap the given text (which may consist of multiple lines) to the
    specified width, preserving natural indentation which is already
    present on each line.

    Args:
        text (str): The text to be wrapped.
        width (int): The maximum width of each line.

    Returns:
        str: The wrapped text with preserved indentation.
    """
    wrapped = []
    lines = text.split('\n')
    for line in lines:
        wrapped.append(wrap_line_with_indent(line, width))
    return '\n'.join(wrapped)

def cwrite(text, color):
    cprint(text, color, end='')

def write(text):
    print(text, end='')

def prompt(txt, color=PROMPT_COLOR, strip=True):
    txt += ' '
    if color: 
        cwrite(txt, color)
    else:
        write(txt)
    response = input()
    if strip: response = response.strip()
    return response

def prompt_options(cmds):
    write(cmds)
    return prompt('>')

def warn(text):
    cprint(text, WARNING_COLOR)

def warn_confirm(question):
    response = prompt(question + " y/N", WARNING_COLOR).strip().lower()
    return input_matches(response, "yes")

def input_matches(response, constant):
    return response and constant.startswith(response.lower())

