"""Development related tasks."""
# pylint: disable=too-many-arguments
# pylint: disable=dangerous-default-value
import sys
import typer
from rich.table import Table
from tasks.common import run_cmd, render_bool, console


app = typer.Typer(help="[b i blue]Linters[/b i blue] and [b i blue]Testers[/b i blue] tasks")


# ------------------------------------------------------------------------------
# Linters and testers
# ------------------------------------------------------------------------------
@app.command(rich_help_panel="Linters")
def black(autoformat: bool = False):
    """Check Python code style with [b i orange1]Black[/b i orange1]."""
    if autoformat:
        black_command = "black"
    else:
        black_command = "black --check --diff"

    command = f"{black_command} ."

    return run_cmd(exec_cmd=command, task_name="black")


@app.command(rich_help_panel="Linters")
def flake8():
    """Check for PEP8 compliance and other style issues."""
    return run_cmd(exec_cmd="flake8 .", task_name="flake8")


@app.command(rich_help_panel="Linters")
def pydocstyle():
    """Run [b i orange1]pydocstyle[/b i orange1] to validate docstrings formatting."""
    return run_cmd(exec_cmd="pydocstyle", task_name="pydocstyle")


@app.command(rich_help_panel="Linters")
def bandit():
    """Run [b i orange1]bandit[/b i orange1] to validate basic static code security analysis."""
    return run_cmd(exec_cmd="bandit --configfile pyproject.toml --recursive .", task_name="bandit")


@app.command(rich_help_panel="Linters")
def pylint():
    """Run [b i orange1]pylint[/b i orange1] code analysis."""
    # command = 'find . -name "*.py" -not -path "*/.venv/*" | xargs pylint --rcfile pyproject.toml'
    command = "pylint --recursive true --ignore=.venv ."
    return run_cmd(exec_cmd=command, task_name="pylint")


@app.command(rich_help_panel="Linters", name="all")
def linters():
    """Run [b i cyan]all[/b i cyan] linters."""
    console.log("Running all linters", style="info")

    # Creates mapping of tests executed along with their end status (True success, False failed)
    tests_execute = {
        "black": black(),
        "flake8": flake8(),
        "pylint": pylint(),
        "pydocstyle": pydocstyle(),
        "bandit": bandit(),
    }

    # Presents results in a Rich table
    table = Table("Test", "Result Ok?", show_lines=True)
    for test, _result in tests_execute.items():
        bool_result = _result.returncode == 0
        table.add_row(test, render_bool(bool_result))
    console.print(table)

    console.log("All tests have executed", style="info")
    if not all(tests_execute.values()):
        sys.exit(1)


@app.command(rich_help_panel="Testers")
def pytest():
    """Run tests."""
    command = "pytest"

    return run_cmd(exec_cmd=command, task_name="pytest")
