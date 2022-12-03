# launch 3 threads
import logging
import os
import subprocess
import threading

# Logging
logging.basicConfig(filename='../debug.log', encoding='utf-8', level=logging.DEBUG)

# Keyboard Only
import threading
import logging
from typing import Iterable
from src.constants import Constants, Raw, Nonblocking
import sys
from select import select


class Keyboard(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.exit = False

    def yield_key(self) -> Iterable[str]:
        """Get a key or escape sequence from stdin, convert to readable format and save to keys list. Meant to be run in it's own thread."""
        input_key: str = ""
        clean_key: str = ""
        mouse_pos = ()
        with Raw(sys.stdin):
            if not select([sys.stdin], [], [], 0.1)[0]:
                pass
            input_key += sys.stdin.read(1)  # * Read 1 key safely with blocking on
            if input_key == "\033":  # * If first character is a escape sequence keep reading
                with Nonblocking(sys.stdin):  # * Set non blocking to prevent read stall
                    input_key += sys.stdin.read(20)
                    if input_key.startswith("\033[<"):
                        _ = sys.stdin.read(1000)
            if input_key == "\033":
                clean_key = "escape"  # * Key is "escape" key if only containing \033
            elif input_key.startswith(("\033[<0;", "\033[<35;", "\033[<64;", "\033[<65;")):
                try:
                    mouse_pos = (int(input_key.split(";")[1]), int(input_key.split(";")[2].rstrip("mM")))
                except:
                    pass
                else:
                    if input_key.startswith("\033[<35;"):  # * Detected mouse move in mouse direct mode
                        pass
                    elif input_key.startswith("\033[<64;"):  # * Detected mouse scroll up
                        clean_key = "mouse_scroll_up"
                    elif input_key.startswith("\033[<65;"):  # * Detected mouse scroll down
                        clean_key = "mouse_scroll_down"
                    elif input_key.startswith("\033[<0;") and input_key.endswith("m"):  # * Detected mouse click release
                        clean_key = "mouse_click"
                    else:
                        clean_key = "NINE"

            elif input_key.startswith("\033[<"):  # * If key is an escape sequence
                clean_key = "random_mouse_click"
                try:
                    mouse_pos = (int(input_key.split(";")[1]), int(input_key.split(";")[2].rstrip("mM")))
                except:
                    pass
            elif input_key == "\\":
                clean_key = "\\"  # * Clean up "\" to not return escaped
            else:
                for code in Constants.escape.keys():  # * Go through dict of escape codes to get the cleaned key name
                    if input_key.lstrip("\033").startswith(code):
                        clean_key = Constants.escape[code]
                        break
                else:  # * If not found in escape dict and length of key is 1, assume regular character
                    if len(input_key) == 1:
                        clean_key = input_key
            yield clean_key, input_key, mouse_pos
            clean_key = ""
            input_key = ""

    def run(self):
        print(Constants.mouse_on)
        while not self.exit:
            p.stdin.write(input("hh>").encode())
            p.stdin.flush()

            continue
            output = self.yield_key()
            for i in output:
                if i[0] == "escape":  # TODO
                    self.exit = True
                    exit(0)
                    break
                if i[0] == "mouse_click":
                    print("mouse_click at", i[2])
                if i[0] == "enter":
                    print("enter")
                    Globals.readin.send("1+1;;")
                    print("enter end")
                logging.debug(i)


# Keyboard Only end

# 1st thread: Ocaml_stdout
# 2nd thread: Ocaml_stderr
# 3rd thread: Ocaml_stdin
# 2nd thread: Keyboard
# 3rd thread: Draw

class Ocaml_stdout(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.exit = False

    def run(self):
        while not self.exit:
            msg = p.stdout.readline()
            print("stdout: ", msg.decode())


class Ocaml_stderr(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.exit = False

    def run(self):
        while not self.exit:
            msg = p.stderr.readline()
            print("stderr: ", msg.decode())
            logging.error(msg.decode(), exc_info=True)



class Draw(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.exit = False

    def GetScreenSize(self):
        Globals.screen_size = os.get_terminal_size()[0], os.get_terminal_size()[1]

    def run(self):
        while not self.exit:
            pass

    def draw_bar(self):
        pass

    def draw_scroll(self):
        pass

    def draw_center(self):
        pass


class Globals:
    screen_size = (0, 0)
    readerr = None
    readout = None
    readin = None
    keyboard = None
    draw = None


if __name__ == '__main__':
    p = subprocess.Popen(["ocaml"], stderr=subprocess.PIPE, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    readout = Ocaml_stdout()
    readout.start()
    Globals.readout = readout

    readerr = Ocaml_stderr()
    readerr.start()
    Globals.readerr = readerr

    keyboard = Keyboard()
    keyboard.start()
    Globals.keyboard = keyboard

    draw = Draw()
    draw.start()
    Globals.draw = draw

    readout.join()
    readerr.join()
    readin.join()
    keyboard.join()
    draw.join()
