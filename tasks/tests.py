"""Development related tasks."""
# pylint: disable=too-many-arguments
# pylint: disable=dangerous-default-value
import sys
from invoke import task
from rich.table import Table  # type: ignore
from .common import run_cmd, console, render_bool, task_executor


# ------------------------------------------------------------------------------
# TEST
# ------------------------------------------------------------------------------
@task
def pytest(context, exit_on_failure=True):
    """Run pytest.

    Example: Run pytest for collected metrics against expected values and tests
        invoke dev.pytest --run-metrics-tests --delay=100

    NOTE: `delay` argument is used for waiting for the stack to be initialized and gather metrics.

    """
    console.log("Running pytest", style="info")
    exec_cmd = "pytest -q tests/"
    result = task_executor(run_cmd(context=context, exec_cmd=exec_cmd, exit_on_failure=exit_on_failure), "pytest")
    return result


@task
def black(context, exit_on_failure=True):
    """Run black to check that Python files adherence to black standards."""
    console.log("Running black code formatter", style="info")
    exec_cmd = "black --check --diff ."
    return task_executor(run_cmd(context, exec_cmd, exit_on_failure), "black")


@task
def flake8(context, exit_on_failure=True):
    """Run flake8 for the specified name and Python version."""
    console.log("Running python flake8", style="info")
    exec_cmd = "flake8 ."
    return task_executor(run_cmd(context, exec_cmd, exit_on_failure), "flake8")


@task
def pylint(context, exit_on_failure=True):
    """Run pylint for the specified name and python/telegraf version."""
    console.log("Running python pylint", style="info")
    exec_cmd = 'find . -name "*.py" | xargs pylint'
    return task_executor(run_cmd(context, exec_cmd, exit_on_failure), "pylint")


@task
def pydocstyle(context, exit_on_failure=True):
    """Run pydocstyle to validate docstrings."""
    console.log("Running pydocstyle", style="info")
    exec_cmd = "pydocstyle ."
    return task_executor(run_cmd(context, exec_cmd, exit_on_failure), "pydocstyle")


@task(name="all")
def all_tests(context):
    """Run all tests."""
    console.log("Running all tests", style="info")

    tests_execute = {
        "black": black(context, exit_on_failure=False),
        "flake8": flake8(context, exit_on_failure=False),
        "pylint": pylint(context, exit_on_failure=False),
        "pydocstyle": pydocstyle(context, exit_on_failure=False),
        "pytest": pytest(context, exit_on_failure=False),
    }

    table = Table("Test", "Result Ok?", show_lines=True)
    for test in tests_execute:
        table.add_row(test, render_bool(tests_execute[test]))
    console.print(table)

    console.log("All tests have executed", style="info")
    if not all(tests_execute.values()):
        sys.exit(1)
