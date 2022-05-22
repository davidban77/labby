"""Common utilities for task commands."""
# pylint: disable=too-many-arguments
# pylint: disable=dangerous-default-value
import os
import sys
from typing import Any, Dict
from pathlib import Path

import toml
from dotenv import dotenv_values
from invoke.context import Context
from invoke.runners import Result
from rich.console import Console
from rich.theme import Theme

# Load environment variables from .env file and from the OS environment
ENVVARS = {**dotenv_values(".env"), **dotenv_values("./deployments/envs/creds.env"), **os.environ}

custom_theme = Theme({"info": "cyan", "warning": "bold magenta", "error": "bold red", "good": "bold green"})

console = Console(color_system="truecolor", log_path=False, record=True, theme=custom_theme, force_terminal=True)


with open("pyproject.toml", "r", encoding="utf8") as pyproject:
    parsed_toml = toml.load(pyproject)

PYTHON_VER = parsed_toml["tool"]["poetry"]["dependencies"]["python"].replace("^", "")
PROJECT_VERSION = parsed_toml["tool"]["poetry"]["version"]


def strtobool(value: Any) -> bool:
    """Return whether the provided string (or any value really) represents true. Otherwise false."""
    if not value:
        return False
    return str(value).lower() in ("y", "yes", "t", "true", "on", "1")


def is_truthy(arg):
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
    return bool(strtobool(arg))


def run_cmd(
    context: Context,
    exec_cmd: str,
    envvars: Dict[str, str] = {},
    hide: Any = None,
    exit_on_failure: bool = True,
    task_name: str = "",
) -> Result:
    """Run invoke task commands.

    Args:
        context (Context): Invoke Context object.
        exec_cmd (str): Command to execute.
        envvars (Dict[str, str], optional): Environment variable to pass. Defaults to {}.
        exit_on_failure (bool, optional): Flag to indicate if the execution should exit if it fails. Defaults to True.

    Exits:
        It exits program execution if flag `exit_on_failure` is set to True and the command ends with code != 0.

    Returns:
        Result: A container for information about the result of a command execution.
    """
    console.log(f"Running command [orange1 i]{exec_cmd}", style="info")
    result: Result = context.run(
        exec_cmd,
        pty=True,
        warn=True,
        env=envvars,
        hide=hide,
    )
    console.log(f"End of command: [orange1 i]{exec_cmd}", style="info")

    if exit_on_failure and not result.ok:
        console.log(f"Error has occurred\n{result.stderr}", style="error")
        sys.exit(result.return_code)

    # Pretty print it
    task_name = task_name if task_name else exec_cmd
    if result.ok:
        console.log(f"Successfully ran {task_name}", style="good")
    else:
        console.log(f"Issues encountered running {task_name}", style="warning")
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
