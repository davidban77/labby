"""Development related tasks for docker."""
# pylint: disable=too-many-arguments
# pylint: disable=dangerous-default-value
import typer
from tasks.common import console, run_cmd, PYTHON_VER, LABBY_VERSION, ENVVARS


REGISTRY = ENVVARS.get("REGISTRY", "davidban77")
TARGET = ENVVARS.get("TARGET", "labby")
REPOSITORY_TAG = f"{REGISTRY}/{TARGET}:v{LABBY_VERSION}-py{PYTHON_VER}"


app = typer.Typer(help="Run Docker commands.")


def docker_build(tag: str, docker_file_target: str, no_cache: bool = False) -> str:
    """Generate the docker build command.

    Args:
        tag (str): Desired tag to use for building the image
        docker_file_target (str): Specific target of the Dockerfile to invoke.
        no_cache (bool): Flag to specify if cache should be ignored. Defaults to False

    Returns:
        str: Docker build command
    """
    command = f"docker build --tag {tag}"
    if no_cache:
        command += " --no-cache"
    command += f" --build-arg PYTHON_VER={PYTHON_VER}" f" -f ./Dockerfile --target {docker_file_target} ."
    return command


@app.command()
def build(
    tag: str = typer.Option(REPOSITORY_TAG, "--tag", help="Docker image tag"),
    target: str = typer.Option(TARGET, "--target", help="Dockerfile target to build"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Flag to specify if cache should be ignored"),
):
    """Build a new Labby container image."""
    console.log(
        f"Building new image [bi]Labby: {LABBY_VERSION} - Python: {PYTHON_VER} - Target: {target}", style="info"
    )
    return run_cmd(
        exec_cmd=docker_build(tag=tag, docker_file_target=target, no_cache=no_cache),
        envvars={
            "PYTHON_VER": PYTHON_VER,
            "LABBY_VERSION": LABBY_VERSION,
            **ENVVARS,
        },
        task_name=f"build {target} image",
    )


@app.command()
def push(
    tag: str = typer.Option(REPOSITORY_TAG, "--tag", help="Docker image tag"),
):
    """Push Labby container image to registry."""
    console.log(f"Pushing new image [i bold]Labby: {LABBY_VERSION} - Python: {PYTHON_VER} - Tag: {tag}", style="info")
    return run_cmd(
        exec_cmd=f"docker push {tag}",
        envvars={
            "PYTHON_VER": PYTHON_VER,
            "LABBY_VERSION": LABBY_VERSION,
            **ENVVARS,
        },
        task_name="pushing labby image",
    )


@app.command()
def login(
    user: str = typer.Option("", "--user", help="User to connect to registry"),
):
    """User to connect to registry."""
    console.log("Connecting to registry", style="info")
    return run_cmd(
        exec_cmd=f"docker login -u {user}",
        envvars=ENVVARS,
        task_name="login to registry",
    )
