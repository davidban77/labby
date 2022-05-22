"""Development related tasks."""
# pylint: disable=too-many-arguments
# pylint: disable=dangerous-default-value
import sys
from rich.table import Table
from invoke import task
from tasks.common import render_bool, console, run_cmd


# ------------------------------------------------------------------------------
# Linters and checkers
# ------------------------------------------------------------------------------
@task(
    help={
        "autoformat": "Apply formatting recommendations automatically, rather than failing if formatting is incorrect.",
    }
)
def black(context, autoformat=False, exit_on_failure=False):
    """Check Python code style with Black."""
    if autoformat:
        black_command = "black"
    else:
        black_command = "black --check --diff"

    command = f"{black_command} ."

    return run_cmd(context, exec_cmd=command, exit_on_failure=exit_on_failure, task_name="black")


@task
def flake8(context, exit_on_failure=True):
    """Check for PEP8 compliance and other style issues."""
    command = "flake8 ."

    return run_cmd(context, exec_cmd=command, exit_on_failure=exit_on_failure, task_name="flake8")


@task
def pydocstyle(context, exit_on_failure=True):
    """Run pydocstyle to validate docstring formatting adheres to NTC defined standards."""
    command = "find . -name '*.py' -not -path '*/.venv/*' | xargs pydocstyle"
    return run_cmd(context, exec_cmd=command, exit_on_failure=exit_on_failure, task_name="pydocstyle")


@task
def bandit(context, exit_on_failure=True):
    """Run bandit to validate basic static code security analysis."""
    command = "bandit --configfile pyproject.toml --recursive ."
    return run_cmd(context, exec_cmd=command, exit_on_failure=exit_on_failure, task_name="bandit")


@task
def pylint(context, exit_on_failure=True):
    """Run pylint code analysis."""
    command = 'find . -name "*.py" -not -path "*/.venv/*" | xargs pylint --rcfile pyproject.toml'
    return run_cmd(context, exec_cmd=command, exit_on_failure=exit_on_failure, task_name="pylint")


@task
def linters(context):
    """Run all linters."""
    console.log("Running all linters", style="info")

    # Creates hash of tests executed along with their end status (True success, False failed)
    tests_execute = {
        "black": black(context, exit_on_failure=False).ok,
        "flake8": flake8(context, exit_on_failure=False).ok,
        "pylint": pylint(context, exit_on_failure=False).ok,
        "pydocstyle": pydocstyle(context, exit_on_failure=False).ok,
        "bandit": bandit(context, exit_on_failure=False).ok,
    }

    # Presents results in a Rich table
    table = Table("Test", "Result Ok?", show_lines=True)
    for test, _result in tests_execute.items():
        table.add_row(test, render_bool(_result))
    console.print(table)

    console.log("All tests have executed", style="info")
    if not all(tests_execute.values()):
        sys.exit(1)
