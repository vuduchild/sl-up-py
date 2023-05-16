import unittest
from src.log_parser import SmartLogParser, LogLineElement

SMART_LOG_OUTPUT_EXAMPLE_1 = """
  o  7a8a6054a  May 09 at 11:16  roy.rothenberg  #3 Unreviewed ✗
  │  commit 3
  │
  @  04b66ceaf  May 09 at 11:22  roy.rothenberg
╭─╯  commit 2
│
│ o  b693b742c  May 09 at 13:56  roy.rothenberg  #2 Merged ✓
├─╯  commit 2
│
o  b7e6cf068  May 09 at 11:21  roy.rothenberg  remote/main
│  commit 1
~

"""
COMMIT_LINE_INDICES_EXAMPLE_1 = [0, 3, 6, 9]
NON_COMMIT_LINE_INDICES_EXAMPLE_1 = [1, 2, 4, 5, 7, 8, 10]
LOCAL_FORK_COMMIT_LINE_INDICES_EXAMPLE_1 = [0, 3, 6]
TRUNK_COMMIT_LINE_INDICES_EXAMPLE_1 = [9]
CURRENT_CHECKOUT_COMMIT_LINE_INDEX_EXAMPLE_1 = 1


class TestLogParser(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_get_commit_lines_indices(self) -> None:
        parser = SmartLogParser(self._smart_log_output())
        self.assertEqual(
            parser.get_commit_lines_indices(), COMMIT_LINE_INDICES_EXAMPLE_1
        )

    def test_current_checkout_commit_line_index(self) -> None:
        parser = SmartLogParser(self._smart_log_output())
        self.assertEqual(
            parser.current_checkout_commit_line_index(),
            CURRENT_CHECKOUT_COMMIT_LINE_INDEX_EXAMPLE_1,
        )

    def test_is_commit_line(self) -> None:
        for line in self._commit_lines():
            self.assertTrue(SmartLogParser.is_commit_line(line))
        for line in self._non_commit_lines():
            self.assertFalse(SmartLogParser.is_commit_line(line))

    def test_is_current_checkout(self) -> None:
        self.assertTrue(SmartLogParser.is_current_checkout(self._smart_log_lines()[3]))
        self.assertFalse(SmartLogParser.is_current_checkout(self._smart_log_lines()[0]))

    def test_is_local_fork(self) -> None:
        for index in LOCAL_FORK_COMMIT_LINE_INDICES_EXAMPLE_1:
            self.assertTrue(
                SmartLogParser.is_local_fork(self._smart_log_lines()[index]),
                f"line {self._smart_log_lines()[index]} is not a local fork",
            )

    def test_is_in_trunk(self) -> None:
        for index in TRUNK_COMMIT_LINE_INDICES_EXAMPLE_1:
            self.assertTrue(
                SmartLogParser.is_in_trunk(self._smart_log_lines()[index]),
                f"line {self._smart_log_lines()[index]} is not in trunk",
            )

    def test_get_elements_from_log_line(self) -> None:
        expected = {
            "author": "roy.rothenberg",
            "commit": "7a8a6054a",
            "datetime": "May 09 at 11:16",
            "pull_request": "#3",
            "status": "Unreviewed",
            "status_emoji": "✗",
        }
        actual = SmartLogParser.get_elements_from_log_line(self._smart_log_lines()[0])
        self.assertEqual(
            self._log_line_elements_simplified(actual),
            expected,
        )

        expected = {
            "author": "roy.rothenberg",
            "commit": "04b66ceaf",
            "datetime": "May 09 at 11:22",
        }
        actual = SmartLogParser.get_elements_from_log_line(self._smart_log_lines()[3])
        self.assertEqual(
            self._log_line_elements_simplified(actual),
            expected,
        )

        expected = {
            "author": "roy.rothenberg",
            "commit": "b7e6cf068",
            "datetime": "May 09 at 11:21",
            "bookmark": "remote/main",
        }
        actual = SmartLogParser.get_elements_from_log_line(self._smart_log_lines()[9])
        self.assertEqual(
            self._log_line_elements_simplified(actual),
            expected,
        )

    def test_get_commit(self) -> None:
        self.assertEqual(
            SmartLogParser.get_commit(self._smart_log_lines()[0]), "7a8a6054a"
        )

    def _smart_log_output(self) -> str:
        return SMART_LOG_OUTPUT_EXAMPLE_1.strip("\n")

    def _smart_log_lines(self) -> list[str]:
        return self._smart_log_output().splitlines()

    def _commit_lines(self) -> list[str]:
        smart_log_lines = self._smart_log_lines()
        return [smart_log_lines[i] for i in COMMIT_LINE_INDICES_EXAMPLE_1]

    def _non_commit_lines(self) -> list[str]:
        smart_log_lines = self._smart_log_lines()
        return [smart_log_lines[i] for i in NON_COMMIT_LINE_INDICES_EXAMPLE_1]

    def _log_line_elements_simplified(
        self, log_line_elements: dict[str, LogLineElement]
    ) -> dict[str, str]:
        return {key: value.text for key, value in log_line_elements.items()}
