from __future__ import annotations

import re
from collections import deque
from pprint import pp
from typing import NamedTuple

GRAPH_OR_WHITE_SPACE_REGEX = r"[╷\│\:\s]*"
COMMIT_MARKER_REGEX = r"[o@]"

COMMIT_LINE_REGEX = rf"""
^                               # start of line
{GRAPH_OR_WHITE_SPACE_REGEX}                      # whitespace or graph lines, 0 or more
{COMMIT_MARKER_REGEX}                            # commit marker
\s+                             # whitespace, 1 or more
(?P<commit>[^\s]+)              # commit hash
\s+                             # whitespace, 1 or more
(?P<datetime>                   # date and time in words
    (                           # Option 1 (example: May 09 at 11:16)
        (\b[^\s]+\b\s)+         # one or more words (day of week, or month and day)
        (at)\s+                 # the word 'at'
        [^\s]+                  # time
    )
    |
    (                           # Option 2 (example: 2 days ago)
        (\b[^\s]+\b\s)+         # one or more words (day of week, or month and day)
        (ago)                   # the word 'ago'
    )
)

(?:\s*|$)                       # whitespace or end of line
(?P<author>[^\s]+)              # author username
\s*                             # whitespace, 0 or more
(?:(?P<pull_request>\#\d+))?     # optional pull request number
\s*                             # whitespace, 0 or more
(?P<status>(                    # optional PR status
    Unreviewed
    |
    Review\ Required
    |
    Merged
    |
    Accepted
    |
    Closed
    )
)?
\s*
(?P<status_emoji>(✓|✗))?        # optional PR status emoji)
(?P<bookmark>(remote)\/[^\s]+)? # optional bookmark
$                               # end of line
"""

MESSAGE_LINE_REGEX = r"""
^                               # start of line
[╷\│\s╭─╯├]+                    # whitespace or graph lines, 1 or more
(?P<message>([^\s]+\s*)+)+      # one or more words
$                               # end of line
"""


class LogLine(NamedTuple):
    text: str
    in_trunk: bool
    elements: dict[str, LogLineElement]


class LogLineElement(NamedTuple):
    text: str
    column_range: tuple[int, int]
    line_number: int


class SelectableEntry(NamedTuple):
    raw_text: str
    selected: bool
    line_indices: list[int]
    elements: dict[str, LogLineElement]


class SmartLogParser:
    def __init__(self, smartlog: str) -> None:
        self.smartlog: list[str] = self._remove_colors(smartlog).splitlines()

    def dump(self) -> None:
        print("\n".join(self.smartlog))
        for line in self.smartlog:
            pp(self.get_log_line_obj(line)._asdict())

    def get_selectable_entries(self) -> list[SelectableEntry]:
        lines = deque(enumerate(self.smartlog))
        selectable_entries: list[SelectableEntry] = []
        while lines:
            commit_line_index, cur_line = lines.popleft()
            elements = self.get_elements_from_commit_line(cur_line)
            if not elements:
                continue
            line_indices = [commit_line_index]
            raw_text = cur_line

            # check if the next line is a message line and if so, consume it
            message_line_index, message_line = lines[0]  # peek without consuming
            message_line_elements = self.get_elements_from_message_line(message_line)
            if message_line_elements:
                lines.popleft()  # consume the message line
                elements.update(message_line_elements)
                line_indices.append(message_line_index)
                raw_text += "\n" + message_line

            selectable_entries.append(
                SelectableEntry(
                    raw_text=raw_text,
                    selected=self.is_current_checkout(cur_line),
                    line_indices=line_indices,
                    elements=elements,
                )
            )

        return selectable_entries

    def get_commit_lines_indices(self) -> list[int]:
        return [
            index
            for index, line in enumerate(self.smartlog)
            if self.is_commit_line(line)
        ]

    def current_checkout_commit_line_index(self) -> int:
        for i, line in enumerate(self.smartlog):
            if self.is_current_checkout(line):
                return self.get_commit_lines_indices().index(i)
        raise ValueError("Could not find current checkout commit line index")

    @classmethod
    def _remove_colors(cls, string: str) -> str:
        # remove ANSI color codes from a
        # https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-pythonq
        ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", string)

    @classmethod
    def is_commit_line(cls, string: str) -> bool:
        matcher = re.compile(rf"^{GRAPH_OR_WHITE_SPACE_REGEX}{COMMIT_MARKER_REGEX}")
        return matcher.match(string) is not None

    @classmethod
    def is_current_checkout(cls, string: str) -> bool:
        matcher = re.compile(rf"^{GRAPH_OR_WHITE_SPACE_REGEX}@")
        return matcher.match(string) is not None

    @classmethod
    def is_local_fork(cls, string: str) -> bool:
        matcher = re.compile(rf"^[\│\s]+{COMMIT_MARKER_REGEX}")
        return matcher.match(string) is not None

    @classmethod
    def is_in_trunk(cls, string: str) -> bool:
        return cls.is_commit_line(string) and not cls.is_local_fork(string)

    @classmethod
    def get_log_line_elements(
        cls,
        log_line: str,
    ) -> dict[str, LogLineElement]:
        return (
            cls.get_elements_from_commit_line(log_line)
            if cls.is_commit_line(log_line)
            else cls.get_elements_from_message_line(log_line)
        )

    @classmethod
    def get_elements_from_commit_line(cls, log_line: str) -> dict[str, LogLineElement]:
        return cls.get_elements_from_log_line(log_line, COMMIT_LINE_REGEX)

    @classmethod
    def get_elements_from_message_line(cls, log_line: str) -> dict[str, LogLineElement]:
        return cls.get_elements_from_log_line(log_line, MESSAGE_LINE_REGEX)

    @classmethod
    def get_elements_from_log_line(
        cls, log_line: str, elements_regex: str
    ) -> dict[str, LogLineElement]:
        retval: dict[str, LogLineElement] = {}
        matches = re.compile(elements_regex, re.VERBOSE).search(log_line)
        if matches:
            group_dict = matches.groupdict()
            for key in group_dict.keys():
                if group_dict[key]:
                    retval[key] = LogLineElement(
                        text=group_dict[key],
                        column_range=matches.span(key),
                        line_number=0 if key != "message" else 1,
                    )
        return retval

    @classmethod
    def get_log_line_obj(cls, log_line: str) -> LogLine:
        log_line = cls._remove_colors(log_line).rstrip()
        return LogLine(
            text=log_line,
            in_trunk=cls.is_in_trunk(log_line),
            elements=cls.get_log_line_elements(log_line),
        )

    @classmethod
    def get_commit(cls, log_line: str) -> str:
        log_line = cls._remove_colors(log_line).rstrip()

        elements = cls.get_log_line_elements(log_line)

        if elements.get("commit"):
            return elements["commit"].text

        raise ValueError("Could not find commit in log line")
