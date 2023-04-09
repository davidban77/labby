"""Common utilities for task commands."""
# pylint: disable=too-many-arguments
# pylint: disable=dangerous-default-value
import os
import subprocess  # nosec
import shlex
from typing import Any, Optional
from pathlib import Path

import toml
from dotenv import dotenv_values
from rich.console import Console
from rich.theme import Theme

# Load environment variables from .env file and from the OS environment
ENVVARS = {**dotenv_values(".env"), **os.environ}

custom_theme = Theme({"info": "cyan", "warning": "bold magenta", "error": "bold red", "good": "bold green"})

console = Console(color_system="truecolor", log_path=False, record=True, theme=custom_theme, force_terminal=True)


with open("pyproject.toml", "r", encoding="utf8") as pyproject:
    parsed_toml = toml.load(pyproject)

LABBY_VERSION = parsed_toml["tool"]["poetry"]["version"]
PYTHON_VER = ENVVARS.get("PYTHON_VER")
if not PYTHON_VER:
    PYTHON_VER = parsed_toml["tool"]["poetry"]["dependencies"]["python"].replace("^", "")


def strtobool(val: str) -> bool:
    """Convert a string representation of truth to true (1) or false (0).

    Args:
        val (str): String representation of truth.

    Returns:
        bool: True or False
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError(f"invalid truth value {val}")


def is_truthy(arg: Any) -> bool:
    """Convert "truthy" strings into Booleans.

    Examples:
    ```python
        >>> is_truthy('yes')
        True
    ```

    Args:
        arg (str): Truthy string (True values are y, yes, t, true, on and 1; false values are n, no,
        f, false, off and 0. Raises ValueError if val is anything else.
    """
    if isinstance(arg, bool):
        return arg
    if arg is None:
        return False
    return bool(strtobool(arg))


def run_cmd(
    exec_cmd: str,
    envvars: dict[str, str] = ENVVARS,
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    # shell: bool = False,
    capture_output: bool = False,
    task_name: str = "",
) -> subprocess.CompletedProcess:
    """Run a command and return the result.

    Args:
        exec_cmd (str): Command to execute
        envvars (dict, optional): Environment variables. Defaults to ENVVARS.
        cwd (str, optional): Working directory. Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to None.
        capture_output (bool, optional): Capture stdout and stderr. Defaults to True.
        task_name (str, optional): Name of the task. Defaults to "".

    Returns:
        subprocess.CompletedProcess: Result of the command
    """
    console.log(f"Running command: [orange1 i]{exec_cmd}", style="info")
    result = subprocess.run(  # nosec
        shlex.split(exec_cmd),
        env=envvars,
        cwd=cwd,
        timeout=timeout,
        # shell=shell
        capture_output=capture_output,
        text=True,
        check=False,
    )
    task_name = task_name if task_name else exec_cmd
    if result.returncode == 0:
        console.log(f"Successfully ran: [i]{task_name}", style="good")
    else:
        console.log(f"Issues encountered running: [i]{task_name}", style="warning")
    console.rule(f"End of task: [b i]{task_name}", style="info")
    console.print()
    return result


def render_bool(value: bool) -> str:
    """Returns Rich string that renders from a boolean value.

    Args:
        value (bool): Bool value

    Returns:
        str: Rich-style string
    """
    return "[green b]Yes" if value is True else "[red b]No"


def get_file(file_path: str) -> Path:
    """Verify a file exists and returns its Path object.

    Args:
        file_path (str): File path.

    Raises:
        SystemExit: When file is not found

    Returns:
        Path: Path object of the file.
    """
    _file = Path(file_path)
    if not _file.exists() and _file.is_file():
        console.log(f"No file found at: {_file}", style="error")
        raise SystemExit(1)
    return _file
