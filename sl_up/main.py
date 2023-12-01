from typing import NoReturn
from .log_parser import SmartLogParser
from .terminal import TerminalRenderer
from .operations import OperationTypes, get_smartlog, sl_goto


def assert_never(arg: NoReturn) -> NoReturn:
    assert False, f"Unhandled type: {type(arg).__name__}"


def run() -> None:
    log_parser = SmartLogParser(get_smartlog())
    renderer = TerminalRenderer(log_parser)

    operation, commit = renderer.launch_interactive_tool()

    match operation:
        case OperationTypes.EXIT:
            return None
        case OperationTypes.GOTO_COMMIT:
            return sl_goto(commit)
    # we should never get here.
    # This call helps the type checker verify we've exhausted all possible cases
    assert_never(operation)


if __name__ == "__main__":
    run()
