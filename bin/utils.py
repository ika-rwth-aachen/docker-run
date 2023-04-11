import subprocess
import sys
from typing import Tuple


def log(msg: str, *args, **kwargs):
    """Log message to stderr.
    Args:
        msg (str): log message
    """

    print(msg, file=sys.stderr, *args, **kwargs)


def printDockerCommand(cmd: str):
    """Prints a docker command in human-readable way by line-breaking on each new argument.

    Args:
        cmd (str): docker command
    """

    components = cmd.split()
    log(f"{components[0]} {components[1]}", end="")

    for c in components[2:]:
        if c.startswith("-"):
            log(f" \\\n  {c}", end="")
        else:
            log(f" {c}", end="")
    log("")


def runCommand(cmd: str, *args, **kwargs) -> Tuple[str, str]:
    """Execute system command.

    Args:
        cmd (str): system command

    Returns:
        Tuple[str, str]: stdout, stderr output
    """

    try:
        output = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, *args, **kwargs)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"System command '{cmd}' failed: {exc.stderr.decode()}")

    return output.stdout.decode(), output.stderr.decode()
