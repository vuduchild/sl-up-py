from log_parser import SmartLogParser
from terminal import TerminalRenderer
from operations import OperationTypes, get_smartlog, sl_goto


def main() -> None:
    # Get the list of Git branches
    log_parser = SmartLogParser(get_smartlog())
    renderer = TerminalRenderer(log_parser)

    operation, commit = renderer.launch_interactive_tool()

    if operation == OperationTypes.GOTO_COMMIT:
        sl_goto(commit)
    elif operation == OperationTypes.EXIT:
        return


if __name__ == "__main__":
    main()
