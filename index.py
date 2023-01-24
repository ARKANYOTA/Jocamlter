import logging
import os
import subprocess
import sys
import threading
import time
from typing import Iterable

from pygments import highlight
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers.ml import OcamlLexer
from select import select

from src.constants import Constants, Raw, Nonblocking


class OPTIONS:
    mouse_active = True
    program = "ocaml"
    # program = "python3"
    Lexer = OcamlLexer


p = subprocess.Popen([OPTIONS.program], stderr=subprocess.PIPE, shell=False, stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE)
logging.basicConfig(filename='debug.log', encoding='utf-8', level=logging.ERROR)


# TODO:
# cursor_x (delete, move right left)

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
        # print(Constants.mouse_on)
        while not GLOBALS.exit_program:
            output = self.yield_key()
            for i in output:
                if i[0] == "escape":  # TODO
                    GLOBALS.cell_selected = -1
                    GLOBALS.screen_need_to_be_refresh = True
                if i[0] == "mouse_click":
                    print("mouse_click at", i[2])
                match i[0]:
                    case "tab" | "shift_tab":
                        GLOBALS.cell_selected = \
                            (GLOBALS.cell_selected +
                             (+1 if i[0] == "tab" else -1)) % len(GLOBALS.Cells)
                        GLOBALS.screen_need_to_be_refresh = True
                    case "up" | "down" | "left" | "right":
                        GLOBALS.Cells[GLOBALS.cell_selected].move_cursor(i[0])
                        GLOBALS.screen_need_to_be_refresh = True
                    case "f5":
                        GLOBALS.screen_need_to_be_refresh = True
                    case "f4":
                        GLOBALS.Cells[GLOBALS.cell_selected].execute()
                        GLOBALS.screen_need_to_be_refresh = True
                    case char if len(char) == 1:
                        if GLOBALS.cell_selected != -1:
                            GLOBALS.Cells[GLOBALS.cell_selected].add_char(char)
                            GLOBALS.screen_need_to_be_refresh = True
                    case "enter":
                        if GLOBALS.Cells[GLOBALS.cell_selected].is_in_or_out == "in":
                            GLOBALS.Cells[GLOBALS.cell_selected].add_line()
                        else:
                            GLOBALS.Cells[GLOBALS.cell_selected].goto_next_cell()
                    case "backspace":
                        if GLOBALS.cell_selected != -1:
                            GLOBALS.Cells[GLOBALS.cell_selected].delete_char()
                            GLOBALS.screen_need_to_be_refresh = True
                    case _:
                        print("NONE")
                        print(i[0], i)
                logging.debug(i)


class Draw:
    @classmethod
    def draw_screen(self):
        print("\033[2J\033[1;1H")
        self.draw_menu_bar()
        self.draw_scroll_bar()
        self.draw_title_bar()
        self.draw_main_menu()
        print()
        # Move cursor to the excepted position
        if GLOBALS.cell_selected != -1 and GLOBALS.Cells[GLOBALS.cell_selected].is_in_or_out == "in":
            x, y = GLOBALS.Cells[GLOBALS.cell_selected].get_position_of_box()
            sys.stdout.write(
                f"\033[{GLOBALS.Cells[GLOBALS.cell_selected].cursor_y + y + 1};{GLOBALS.Cells[GLOBALS.cell_selected].cursor_x + x + 1}H")
        else:
            sys.stdout.write(f"\033[{20};{20}H")
        sys.stdout.flush()

    @classmethod
    def draw_main_menu(cls):
        ligne = 2
        for cell in GLOBALS.Cells:
            cell.draw(ligne)
            ligne += 3 + len(cell.lines)
        pass

    @classmethod
    def draw_title_bar(cls):
        fill = " " * (GLOBALS.screen_width - 1)
        print("\033[1;1H\033[;41m" + fill + "\033[0m")
        print("\033[1;1H\033[33;41mJocamlter\033[0m")
        pass

    @classmethod
    def draw_menu_bar(cls):
        fill = " " * (GLOBALS.screen_width - 2)
        print(f"\033[{GLOBALS.screen_height};1H\033[;44m" + fill + "\033[0m", end="")
        print(f"\033[{GLOBALS.screen_height};1H\033[33;44mS Save File\033[0m", end="")
        print(f"\033[{GLOBALS.screen_height};13H\033[33;44mN New File (Erase other file)\033[0m", end="")
        print("\033[1;1H")

        pass

    @classmethod
    def draw_scroll_bar(cls):
        cls.draw_pixel("^", GLOBALS.screen_width - 1, 0)
        for i in range(1, GLOBALS.screen_height - 1):
            cls.draw_pixel("x", GLOBALS.screen_width - 1, i)
        cls.draw_pixel("^", GLOBALS.screen_width - 1, GLOBALS.screen_height - 1)
        pass

    @classmethod
    def draw_pixel(cls, pixel, x, y, x_top=0, y_top=0, color=0, background_color=0):
        # Top left corner of the screen is 0,0
        if color != 0 or background_color != 0:
            color_text = ""
            if color != 0:
                color_text += "\033[" + str(color) + "m"
            if background_color != 0:
                color_text += "\033[" + str(background_color) + "m"
            print(f"{color_text}\033[{y + y_top + 1};{x + x_top + 1}H{color_text}{pixel}\033[0m", end="")
        else:
            print(f"\033[{y + y_top + 1};{x + x_top + 1}H{pixel}", end="")
        return

    @classmethod
    def draw_box(cls, x1, y1, x2, y2, x_top=0, y_top=0, color=0, background_color=0):
        # Top left corner of the screen is 0,0
        cls.draw_pixel("┌", x1, y1, x_top, y_top, color, background_color)
        cls.draw_pixel("┐", x2, y1, x_top, y_top, color, background_color)
        cls.draw_pixel("└", x1, y2, x_top, y_top, color, background_color)
        cls.draw_pixel("┘", x2, y2, x_top, y_top, color, background_color)
        for x in range(x1 + 1, x2):
            cls.draw_pixel("─", x, y1, x_top, y_top, color, background_color)
            cls.draw_pixel("─", x, y2, x_top, y_top, color, background_color)
        for y in range(y1 + 1, y2):
            cls.draw_pixel("│", x1, y, x_top, y_top, color, background_color)
            cls.draw_pixel("│", x2, y, x_top, y_top, color, background_color)


class Cell:
    def __init__(self, is_in_or_out, id, nb_exec, has_error=False):
        self.is_in_or_out = is_in_or_out
        self.id = id
        self.nb_exec = nb_exec
        self.has_error = has_error
        self.cursor_x = 0
        self.cursor_y = 0
        self.lines = [""]

    def draw(self, ligne):
        if self.is_in_or_out == "out":
            color = 31 if self.has_error else 32
        else:
            color = 0
        if GLOBALS.cell_selected == self.id:
            backcolor = 100
        else:
            backcolor = 0
        Draw.draw_box(10, ligne, GLOBALS.screen_width - 3, ligne + 1 + len(self.lines), color=color,
                      background_color=backcolor)

        if self.is_in_or_out != "out":
            if GLOBALS.await_code_in_cell == self.id:
                Draw.draw_pixel(f"{self.is_in_or_out.capitalize():>3}[*]:", 2, ligne + 1)
            else:
                Draw.draw_pixel(f"{self.is_in_or_out.capitalize():>3}[{self.nb_exec}]:", 2, ligne + 1)

        code = highlight(code="\n".join(self.lines), formatter=TerminalFormatter(), lexer=OPTIONS.Lexer())
        for i, line in enumerate(code.split("\n")):
            # mltohtml.parse("\n".join(self.lines)).split("\n")
            Draw.draw_pixel(line, 11, ligne + 1 + i)

    def move_cursor(self, direction):
        if GLOBALS.Cells[GLOBALS.cell_selected].is_in_or_out == "out":
            return
        match direction:
            case "up":
                if self.cursor_y > 0:
                    self.cursor_y -= 1
                    if len(self.lines[self.cursor_y]) < self.cursor_x:
                        self.cursor_x = len(self.lines[self.cursor_y])
            case "down":
                if self.cursor_y < len(self.lines) - 1:
                    self.cursor_y += 1
                    if len(self.lines[self.cursor_y]) < self.cursor_x:
                        self.cursor_x = len(self.lines[self.cursor_y])
            case "left":
                if self.cursor_x > 0:
                    self.cursor_x -= 1
            case "right":
                if self.cursor_x < len(GLOBALS.Cells[GLOBALS.cell_selected].lines[self.cursor_y]):
                    self.cursor_x += 1
            case _:
                return

    def add_char(self, char):
        if GLOBALS.Cells[GLOBALS.cell_selected].is_in_or_out == "out":
            return
        GLOBALS.Cells[GLOBALS.cell_selected].lines[self.cursor_y] += char
        GLOBALS.Cells[GLOBALS.cell_selected].cursor_x += 1

    def delete_char(self):  # TOFIX supprime tout ce qu'il y a apres le cursor x
        if GLOBALS.Cells[GLOBALS.cell_selected].is_in_or_out == "out":
            return
        if self.cursor_x > 0:
            self.lines[self.cursor_y] = self.lines[self.cursor_y][:self.cursor_x - 1]
            self.cursor_x -= 1
        elif self.cursor_y > 0:
            self.cursor_x = len(self.lines[self.cursor_y - 1])
            self.lines[self.cursor_y - 1] += self.lines[self.cursor_y]
            self.lines.pop(self.cursor_y)
            self.cursor_y -= 1

    def add_line(self):
        if GLOBALS.Cells[GLOBALS.cell_selected].is_in_or_out == "out":
            return
        GLOBALS.Cells[GLOBALS.cell_selected].lines.insert(self.cursor_y + 1, "")
        GLOBALS.Cells[GLOBALS.cell_selected].move_cursor("down")
        GLOBALS.screen_need_to_be_refresh = True

    def get_position_of_box(self):
        line = 0
        for i in range(self.id):
            line += len(GLOBALS.Cells[i].lines) + 3
        return 11, 3 + line

    def execute(self):
        if self.is_in_or_out == "out":
            return
        nb_exec = self.nb_exec
        self.nb_exec = "*"
        code = "\n".join(GLOBALS.Cells[GLOBALS.cell_selected].lines)
        if len(GLOBALS.Cells) != GLOBALS.cell_selected+1:
            GLOBALS.Cells[GLOBALS.cell_selected+1].lines = [""]  # clear the cell
        GLOBALS.await_code_in_cell = GLOBALS.cell_selected
        OCAMLSTD.send(code)
        self.nb_exec = nb_exec + 1

    def code_in(self, code):
        if self.is_in_or_out != "in":
            return
        if len(GLOBALS.Cells) == GLOBALS.await_code_in_cell + 1:
            GLOBALS.Cells.append(Cell("out", GLOBALS.await_code_in_cell + 1, 0))
        GLOBALS.Cells[GLOBALS.await_code_in_cell + 1].lines.extend(code.split("\n"))
        GLOBALS.cell_selected = GLOBALS.await_code_in_cell + 1
        GLOBALS.Cells[GLOBALS.cell_selected].goto_next_cell()
        GLOBALS.screen_need_to_be_refresh = True  # TOFIX Savoir le temps du dt

    def goto_next_cell(self):
        if len(GLOBALS.Cells) == GLOBALS.cell_selected+1:
            if self.is_in_or_out == "out":
                GLOBALS.Cells.append(Cell("in", GLOBALS.cell_selected + 1, 0))
            else:
                GLOBALS.Cells.append(Cell("out", GLOBALS.cell_selected + 1, 0))
        GLOBALS.cell_selected += 1
        GLOBALS.screen_need_to_be_refresh = True


class GLOBALS:
    exit_program = False
    screen_need_to_be_refresh = True
    refresh_dt = 0
    screen_width, screen_height = os.get_terminal_size()[0], os.get_terminal_size()[1]

    # Cells id start at 0
    Cells: list[Cell] = [
        Cell("in", 0, 0),
    ]

    scroll_bar_pos = 0

    cell_selected = 0  # If -1, no cell is selected
    await_code_in_cell = -1


class OCAMLSTD:
    def __init__(self):
        self.readerr = None
        self.readout = None

    def read_stdout(self):
        try:
            while not GLOBALS.exit_program:
                msg = p.stdout.readline()
                logging.info("stdout: "+msg.decode().strip())
                code = msg.decode().strip()
                if GLOBALS.await_code_in_cell != -1:
                    GLOBALS.Cells[GLOBALS.await_code_in_cell].code_in(code)
        except Exception:
            logging.error("Fatal error in main loop", exc_info=True)



    def read_stderro(self):
        while not GLOBALS.exit_program:
            msg = p.stderr.readline()
            logging.info("stderr: "+msg.decode().strip())

    def start(self):
        self.readout = threading.Thread(target=self.read_stdout)
        self.readout.start()

        self.readerr = threading.Thread(target=self.read_stderro)
        self.readerr.start()

    def join(self):
        self.readout.join()
        self.readerr.join()

    @classmethod
    def send(cls, msg):
        p.stdin.flush()
        p.stdin.write((msg + "\n").encode())
        p.stdin.flush()


if __name__ == "__main__":
    if OPTIONS.mouse_active:
        print(Constants.mouse_on)
    ocamlstd = OCAMLSTD()
    ocamlstd.start()
    keyboard = Keyboard()
    keyboard.start()

    while not GLOBALS.exit_program:  # Draw
        if GLOBALS.screen_need_to_be_refresh:
            if GLOBALS.refresh_dt > 0:
                time.sleep(GLOBALS.refresh_dt)
                GLOBALS.refresh_dt = 0
            Draw.draw_screen()
            GLOBALS.screen_need_to_be_refresh = False
        pass

    GLOBALS.exit_program = True

    keyboard.join()
    ocamlstd.join()