import re
from typing import NamedTuple


class LogLineElement(NamedTuple):
    text: str
    coordinates: tuple[int, int]


class SmartLogParser:
    def __init__(self, smartlog: str):
        self.smartlog: list[str] = self._remove_colors(smartlog).splitlines()

    def get_commit_lines_indices(self) -> list[int]:
        return [
            i
            for i in range(len(self.smartlog))
            if self.is_commit_line(self.smartlog[i])
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
        matcher = re.compile(r"^[\│\s]*[o@]")
        return matcher.match(string) is not None

    @classmethod
    def is_current_checkout(cls, string: str) -> bool:
        matcher = re.compile(r"^[\│\s]*@")
        return matcher.match(string) is not None

    @classmethod
    def is_local_fork(cls, string: str) -> bool:
        matcher = re.compile(r"^[\│\s]+[o@]")
        return matcher.match(string) is not None

    @classmethod
    def is_in_trunk(cls, string: str) -> bool:
        return cls.is_commit_line(string) and not cls.is_local_fork(string)

    @staticmethod
    def get_elements_from_log_line(
        log_line: str,
    ) -> dict[str, LogLineElement]:
        retval: dict[str, LogLineElement] = {}
        matcher = re.compile(
            r"""
            ^                               # start of line
            [\│\:\s]*                       # whitespace or graph lines, 0 or more
            [o@]                            # commit marker
            \s+                             # whitespace, 1 or more
            (?P<commit>[^\s]+)              # commit hash
            \s+                             # whitespace, 1 or more
            (?P<datetime>                   # date and time in words
                (\b[^\s]+\b\s)+             # one or more words (day of week, or month and day)
                (at)\s+                     # the word 'at'
                [^\s]+                      # time
            )
            \s+                             # whitespace, 1 or more
            (?P<author>[^\s]+)              # author username
            \s*                             # whitespace, 0 or more
            (?:(?P<pull_request>\#\d+))?     # optional pull request number
            \s*                             # whitespace, 0 or more
            (?P<status>(                    # optional PR status
                Unreviewed
                |
                Review Required
                |
                Merged
                |
                Accepted
                )
            )?
            \s*
            (?P<status_emoji>(✓|✗))?        # optional PR status emoji)
            (?P<bookmark>(remote)\/[^\s]+)? # optional bookmark
            $                               # end of line
            """,
            re.VERBOSE,
        )
        matches = matcher.search(log_line)
        if matches:
            group_dict = matches.groupdict()
            for key in group_dict.keys():
                if group_dict[key]:
                    retval[key] = LogLineElement(
                        text=group_dict[key],
                        coordinates=matches.span(key),
                    )
        return retval

    @classmethod
    def get_commit(cls, log_line: str) -> str:
        log_line = cls._remove_colors(log_line).strip()

        elements = cls.get_elements_from_log_line(log_line)

        if elements.get("commit"):
            return elements["commit"].text

        raise ValueError("Could not find commit in log line")
