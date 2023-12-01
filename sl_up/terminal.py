import curses as _curses
import os

from enum import Enum
from typing import Optional, Tuple

from .log_parser import SmartLogParser
from .operations import OperationTypes


class Colors(Enum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7
    GRAY = 11


class TerminalRenderer:
    def __init__(self, log_parser: SmartLogParser) -> None:
        self._log_parser = log_parser
        self._window: Optional[_curses.window] = None

    @property
    def window(self) -> _curses.window:
        if self._window is None:
            self._window = self._init_window()
        return self._window

    def launch_interactive_tool(self) -> Tuple[OperationTypes, str]:
        try:
            return self._launch_interactive_tool_impl()
        finally:
            self._cleanup()

    def _launch_interactive_tool_impl(self) -> Tuple[OperationTypes, str]:
        # These are the only lines we want to interact with
        commit_lines_indices = self._log_parser.get_commit_lines_indices()
        current_checkout = self._log_parser.current_checkout_commit_line_index()
        # start the at the current checkout
        current_line = current_checkout
        # Draw the initial menu
        self._draw_menu(commit_lines_indices[current_line])
        while True:
            try:
                # Listen for user input
                key = self.window.getch()

                match key:
                    case _curses.KEY_UP if current_line > 0:
                        current_line -= 1
                        self._draw_menu(commit_lines_indices[current_line])

                    case _curses.KEY_DOWN if current_line < len(
                        commit_lines_indices
                    ) - 1:
                        current_line += 1
                        self._draw_menu(commit_lines_indices[current_line])

                    case (_curses.KEY_ENTER | 10 | 13):
                        if current_checkout == current_line:
                            return OperationTypes.EXIT, ""

                        ref = self._log_parser.get_commit(
                            self._log_parser.smartlog[
                                commit_lines_indices[current_line]
                            ]
                        )
                        return OperationTypes.GOTO_COMMIT, ref

                    case 27:  # Escape key
                        return OperationTypes.EXIT, ""

                    case _:
                        # ignore all other keys
                        pass

            except KeyboardInterrupt:
                return OperationTypes.EXIT, ""

    def _draw_menu(self, current_line: int) -> None:
        self.window.clear()

        # Draw the branch menu
        for i, log_line in enumerate(self._log_parser.smartlog):
            self._format_line(log_line, i, i in (current_line, current_line + 1))
        self.window.refresh()

    def _format_line(
        self,
        log_line: str,
        insert_line_index: int,
        is_current_line: bool = False,
    ) -> None:
        log_line_obj = SmartLogParser.get_log_line_obj(log_line)

        # First display the whole line
        self._render_text(log_line_obj.text, insert_line_index, 0)

        # current line gets special treatment
        colors_per_element_when_selected = {
            "author": Colors.MAGENTA,
            "datetime": Colors.MAGENTA,
            "message": Colors.MAGENTA,
        }
        if is_current_line:
            for element_name, color in colors_per_element_when_selected.items():
                if log_line_obj.elements.get(element_name):
                    self._render_text(
                        log_line_obj.elements[element_name].text,
                        insert_line_index,
                        log_line_obj.elements[element_name].column_range[0],
                        color,
                    )

        if log_line_obj.elements.get("commit"):
            self._render_text(
                log_line_obj.elements["commit"].text,
                insert_line_index,
                log_line_obj.elements["commit"].column_range[0],
                Colors.YELLOW if log_line_obj.in_trunk else Colors.GRAY,
                bold=not log_line_obj.in_trunk,
            )
        if log_line_obj.elements.get("bookmark"):
            self._render_text(
                log_line_obj.elements["bookmark"].text,
                insert_line_index,
                log_line_obj.elements["bookmark"].column_range[0],
                Colors.GREEN,
            )

    def _render_text(
        self,
        text: str,
        insert_line_index: int,
        insert_row_index: int = 1,
        color: Optional[Colors] = None,
        bold: bool = False,
    ) -> None:
        params: list[int] = []
        if color is not None:
            color_val = _curses.color_pair(color.value + 1)
            if bold:
                color_val |= _curses.A_BOLD
            params.append(color_val)

        self.window.addstr(insert_line_index, insert_row_index, text, *params)

    @classmethod
    def _init_window(cls) -> _curses.window:
        os.environ.setdefault("ESCDELAY", "1")
        stdscr = _curses.initscr()

        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        _curses.noecho()
        _curses.cbreak()

        # In keypad mode, escape sequences for special keys
        # (like the cursor keys) will be interpreted and
        # a special value like curses.KEY_LEFT will be returned
        stdscr.keypad(True)

        # Start color, too.  Harmless if the terminal doesn't have
        # color; user can test with has_color() later on.  The try/catch
        # works around a minor bit of over-conscientiousness in the curses
        # module -- the error return from C start_color() is ignorable.
        try:
            _curses.start_color()

        except Exception:
            pass

        # Hide the cursor
        _curses.curs_set(0)

        _curses.use_default_colors()
        for i in range(0, _curses.COLORS - 1):
            _curses.init_pair(i + 1, i, -1)

        return stdscr

    def _cleanup(self) -> None:
        # Set everything back to normal
        if self._window is not None:
            self._window.keypad(False)
            _curses.echo()
            _curses.nocbreak()
            _curses.endwin()
