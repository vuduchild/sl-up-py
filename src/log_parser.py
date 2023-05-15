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

    @staticmethod
    def _remove_colors(string: str) -> str:
        # remove ANSI color codes from a
        # https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-pythonq
        ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", string)

    @staticmethod
    def is_commit_line(string: str) -> bool:
        matcher = re.compile(r"^[\|\:\s]*[o\*]")
        return matcher.match(string) is not None

    @staticmethod
    def is_current_checkout(string: str) -> bool:
        matcher = re.compile(r"^[\|\:\s]*\*")
        return matcher.match(string) is not None

    @staticmethod
    def remove_graphical_elements(string: str) -> str:
        matcher = re.compile(r"^[\|\:\s]*[o\*]\s*")
        return matcher.sub("", string)

    @staticmethod
    def get_elements_from_log_line(
        log_line: str,
    ) -> dict[str, LogLineElement]:
        retval: dict[str, LogLineElement] = {}
        matcher = re.compile(
            r"^[\|\:\s]*[o\*]\s*(?P<commit>[^\s]+)\s*(?P<author>[^\s]+)\s*(?:\((?P<branches>.*)\)\s*)?(?P<time>.*)$"
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

    def get_commit_or_branch_name(self, log_line: str) -> str:
        log_line = self._remove_colors(log_line).strip()

        elements = self.get_elements_from_log_line(log_line)

        if elements.get("branches"):
            branches = elements["branches"].text.split(",")
            branches = [branch.strip() for branch in branches]
            local_branches = [b for b in branches if not b.startswith("origin/")]
            return local_branches[0] if local_branches else branches[0]

        if elements.get("commit"):
            return elements["commit"].text

        raise ValueError("Could not find commit or branch name in log line")
