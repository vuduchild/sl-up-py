from enum import Enum
import subprocess


class OperationTypes(Enum):
    EXIT = 0
    GOTO_COMMIT = 1


def get_smartlog() -> str:
    return (
        subprocess.check_output(
            ["/Users/royr/repos/personal/sapling/eden/scm/sl", "ssl"]
        )
        .decode()
        .strip("\n")
    )


def sl_goto(ref: str) -> None:
    subprocess.check_call(
        ["/Users/royr/repos/personal/sapling/eden/scm/sl", "goto", ref]
    )
