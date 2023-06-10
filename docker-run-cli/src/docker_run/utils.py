import re
import subprocess
import sys
from typing import Tuple


def log(msg: str, *args, **kwargs):
    """Log message to stderr.
    Args:
        msg (str): log message
    """

    print(msg, file=sys.stderr, *args, **kwargs)


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


def validDockerContainerName(name: str) -> str:
    """Cleans a string such that it is a valid Docker container name.

    [a-zA-Z0-9][a-zA-Z0-9_.-]

    Args:
        name (str): raw name

    Returns:
        str: valid container name
    """
    
    name = re.sub('[^a-zA-Z0-9_.-]', '-', name)
    name = re.sub('^[^a-zA-Z0-9]+', '', name)
    
    return name
