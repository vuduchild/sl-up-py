import curses as _curses
from enum import Enum
from typing import Any, Callable

from log_parser import SmartLogParser


class Colors(Enum):
    WHITE = 0
    MAGENTA = 2
    YELLOW = 3
    GREEN = 4


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
        # Define color pairs for highlighting the current line
        _curses.init_pair(1, _curses.COLOR_WHITE, -1)
        _curses.init_pair(2, _curses.COLOR_MAGENTA, -1)
        _curses.init_pair(3, _curses.COLOR_YELLOW, -1)
        _curses.init_pair(4, _curses.COLOR_GREEN, -1)

        return func(stdscr, *args, **kwargs)
    finally:
        # Set everything back to normal
        if stdscr is not None:
            stdscr.keypad(False)
            _curses.echo()
            _curses.nocbreak()
            _curses.endwin()


def color_screen_text(
    text: str,
    window: _curses.window,
    insert_line_index: int,
    insert_row_index: int = 1,
    color: Colors = Colors.WHITE,
) -> None:
    window.attron(_curses.color_pair(color.value))
    window.addstr(insert_line_index, insert_row_index, text)
    window.attroff(_curses.color_pair(color.value))


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
    insert_row_index = 1
    if is_current_line:
        color_screen_text(
            log_line, window, insert_line_index, insert_row_index, Colors.MAGENTA
        )
    else:
        # first colorize the whole thing white
        color_screen_text(log_line, window, insert_line_index, insert_row_index)

        # colorize specific elements
        elements = SmartLogParser.get_elements_from_log_line(log_line)
        if elements.get("commit"):
            color_screen_text(
                elements["commit"].text,
                window,
                insert_line_index,
                elements["commit"].coordinates[0] + 1,
                Colors.YELLOW,
            )
        if elements.get("branches"):
            color_screen_text(
                f"({elements['branches'].text})",
                window,
                insert_line_index,
                elements["branches"].coordinates[0],
                Colors.GREEN,
            )
