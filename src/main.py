import curses
import os
import subprocess

import terminal

from log_parser import SmartLogParser


def get_smartlog() -> str:
    return subprocess.check_output(["git", "smartlog"]).decode()


def git_checkout(ref: str) -> None:
    subprocess.check_call(["git", "checkout", ref])


def main(window: curses.window) -> None:
    # Get the list of Git branches
    parser = SmartLogParser(get_smartlog())

    # These are the only lines we want to interact with
    commit_lines_indices = parser.get_commit_lines_indices()
    current_checkout = parser.current_checkout_commit_line_index()
    # start the at the current checkout
    current_line = current_checkout
    # Draw the initial menu
    terminal.draw_menu(window, commit_lines_indices[current_line], parser.smartlog)
    while True:
        try:
            # Listen for user input
            key = window.getch()
            if key == curses.KEY_UP and current_line > 0:
                current_line -= 1
            elif (
                key == curses.KEY_DOWN and current_line < len(commit_lines_indices) - 1
            ):
                current_line += 1
            elif key in [curses.KEY_ENTER, 10, 13]:
                # Switch to the selected branch
                ref = parser.get_commit_or_branch_name(
                    parser.smartlog[commit_lines_indices[current_line]]
                )
                if current_checkout != current_line:
                    git_checkout(ref)
                break
            elif key == 27:  # Escape key
                break
            # Redraw the menu with the new selection
            terminal.draw_menu(
                window, commit_lines_indices[current_line], parser.smartlog
            )
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    os.environ.setdefault("ESCDELAY", "1")  # exit fast on escape key
    terminal.wrap(main)
