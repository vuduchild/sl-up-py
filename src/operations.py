from enum import Enum
import subprocess


class OperationTypes(Enum):
    EXIT = 0
    GOTO_COMMIT = 1


def get_smartlog() -> str:
    return subprocess.check_output(["sl", "ssl"]).decode().strip("\n")


def sl_goto(ref: str) -> None:
    subprocess.check_call(["sl", "goto", ref])
