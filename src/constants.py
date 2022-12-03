import termios
import tty
import fcntl
import os
from typing import Union, Tuple, Dict


class Constants:
    hide_cursor = "\033[?25l"  # * Hide terminal cursor
    show_cursor = "\033[?25h"  # * Show terminal cursor
    alt_screen = "\033[?1049h"  # * Switch to alternate screen
    normal_screen = "\033[?1049l"  # * Switch to normal screen
    clear = "\033[2J\033[0;0f"  # * Clear screen and set cursor to position 0,0
    mouse_on = "\033[?1002h\033[?1015h\033[?1006h"  # * Enable reporting of mouse position on click and release
    mouse_off = "\033[?1002l"  # * Disable mouse reporting
    mouse_direct_on = "\033[?1003h"  # * Enable reporting of mouse position at any movement
    mouse_direct_off = "\033[?1003l"  # * Disable direct mouse reporting
    escape: Dict[Union[str, Tuple[str, str]], str] = {
        "\n": "enter",
        ("\x7f", "\x08"): "backspace",
        ("[A", "OA"): "up",
        ("[B", "OB"): "down",
        ("[D", "OD"): "left",
        ("[C", "OC"): "right",
        "[2~": "insert",
        "[3~": "delete",
        "[H": "home",
        "[F": "end",
        "[5~": "page_up",
        "[6~": "page_down",
        "\t": "tab",
        "[Z": "shift_tab",
        "OP": "f1",
        "OQ": "f2",
        "OR": "f3",
        "OS": "f4",
        "[15": "f5",
        "[17": "f6",
        "[18": "f7",
        "[19": "f8",
        "[20": "f9",
        "[21": "f10",
        "[23": "f11",
        "[24": "f12"
    }


class Raw(object):
    """Set raw input mode for device"""

    def __init__(self, stream):
        self.stream = stream
        self.fd = self.stream.fileno()

    def __enter__(self):
        self.original_stty = termios.tcgetattr(self.stream)
        tty.setcbreak(self.stream)

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(self.stream, termios.TCSANOW, self.original_stty)


class Nonblocking(object):
    """Set nonblocking mode for device"""

    def __init__(self, stream):
        self.stream = stream
        self.fd = self.stream.fileno()

    def __enter__(self):
        self.orig_fl = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.orig_fl | os.O_NONBLOCK)

    def __exit__(self, *args):
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.orig_fl)
