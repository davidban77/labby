"""Tasks for Labby Development Tools."""
import typer
import tasks.check
import tasks.docker


app = typer.Typer(help="Labby Development Tools Tasks", rich_markup_mode="rich", add_completion=False)
app.add_typer(tasks.check.app, name="check")
app.add_typer(tasks.docker.app, name="docker")
