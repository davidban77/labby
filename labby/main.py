import typer
import labby.config
import labby.projects
import labby.templates
import labby.nodes
import labby.connections
import labby.provision

# from pathlib import Path
from labby.utils import banner
# from labby.config import LabbyConfig


app = typer.Typer(help="Awesome Network Lab Management Toolish!", callback=banner())
state = {"verbose": False}


app.add_typer(labby.config.app, name="config")
app.add_typer(labby.projects.app, name="project")
app.add_typer(labby.templates.app, name="template")
app.add_typer(labby.nodes.app, name="node")
app.add_typer(labby.connections.app, name="link")
app.add_typer(labby.provision.app, name="provision")


@app.callback()
def main(ctx: typer.Context, verbose: bool = False):
    """
    Awesome Network Lab Management Tool!
    """
    # banner()
    # print("AQUI AQUI")
    # print(ctx.obj)
    # ctx.obj = LabbyConfig()
    # print(ctx.obj)
    if verbose:
        typer.echo("Will write verbose output")
        state["verbose"] = True
    # app_dir = Path(
    #     typer.get_app_dir(APP_NAME, force_posix=True).replace(".labby", ".config/labby")
    # )
    # print(app_dir.is_dir(), app_dir)
    # config_path: Path = Path(app_dir) / "labby.yml"
    # print(config_path)
    # if not config_path.is_file():
    #     print("YUHUYHU-AQUIAQUI")
    #     typer.echo("Config file doesn't exist yet")


if __name__ == "__main__":
    # app_dir = typer.get_app_dir(APP_NAME)
    # config_path: Path = Path(app_dir) / "labby.yml"
    # print("AQUI AQUI AQUI")
    # if not config_path.is_file():
    #     typer.echo("Config file doesn't exist yet")
    app()
