import curses as _curses
from enum import Enum
from typing import Any, Callable, Optional

from log_parser import SmartLogParser


class Colors(Enum):
    WHITE = 0
    BLACK = 1
    RED = 2
    GREEN = 3
    YELLOW = 4
    BLUE = 5
    MAGENTA = 6
    CYAN = 7


def wrap(func: Callable[[_curses.window], None], /, *args: Any, **kwargs: Any) -> Any:
    """Wrapper function that initializes curses and calls another function,
    restoring normal keyboard/screen behavior on error.
    The callable object 'func' is then passed the main window 'stdscr'
    as its first argument, followed by any other arguments passed to
    wrapper().
    """
    stdscr = None
    try:
        # Initialize curses
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
        for i in range(0, _curses.COLORS):
            _curses.init_pair(i + 1, i, -1)

        return func(stdscr, *args, **kwargs)
    finally:
        # Set everything back to normal
        if stdscr is not None:
            stdscr.keypad(False)
            _curses.echo()
            _curses.nocbreak()
            _curses.endwin()


def render_text(
    text: str,
    window: _curses.window,
    insert_line_index: int,
    insert_row_index: int = 1,
    color: Optional[Colors] = None,
) -> None:
    params: list[int] = []
    if color is not None:
        params.append(_curses.color_pair(color.value))

    window.addstr(insert_line_index, insert_row_index, text, *params)


def draw_menu(window: _curses.window, current_line: int, smartlog: list[str]) -> None:
    window.clear()

    # Draw the branch menu
    for i, log_line in enumerate(smartlog):
        format_line(log_line, window, i + 1, i == current_line)
    window.refresh()


def format_line(
    log_line: str,
    window: _curses.window,
    insert_line_index: int,
    is_current_line: bool = False,
) -> None:
    log_line_obj = SmartLogParser.get_log_line_obj(log_line)

    # First display the whole line
    render_text(log_line_obj.text, window, insert_line_index, 0)

    # Colorize the commit hash
    if log_line_obj.elements.get("commit"):
        render_text(
            log_line_obj.elements["commit"].text,
            window,
            insert_line_index,
            log_line_obj.elements["commit"].coordinates[0],
            Colors.YELLOW if log_line_obj.in_trunk else Colors.BLUE,
        )

    # if is_current_line:
    #     color_screen_text(
    #         log_line, window, insert_line_index, insert_row_index, Colors.MAGENTA
    #     )
    # else:
    #     # first colorize the whole thing white
    #     color_screen_text(log_line, window, insert_line_index, insert_row_index)

    #     # colorize specific elements
    #     elements = SmartLogParser.get_log_line_elements(log_line)
    #     if elements.get("commit"):
    #         color_screen_text(
    #             elements["commit"].text,
    #             window,
    #             insert_line_index,
    #             elements["commit"].coordinates[0] + 1,
    #             Colors.YELLOW,
    #         )
    #     if elements.get("bookmark"):
    #         color_screen_text(
    #             elements["bookmark"].text,
    #             window,
    #             insert_line_index,
    #             elements["bookmark"].coordinates[0] + 1,
    #             Colors.GREEN,
    #         )
