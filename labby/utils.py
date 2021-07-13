# from pathlib import Path
import re
import typer
import functools
# from labby import settings
from typing import Dict, List, Any, MutableMapping, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme


custom_theme = Theme({"warning": "bold magenta", "error": "bold red", "good": "bold green"})


console = Console(color_system="auto", log_path=False, record=True, theme=custom_theme)


def banner():
    console.print(
        """
[green]
  _       _     _
 | | __ _| |__ | |__  _   _
 | |/ _` | '_ \| '_ \| | | |
 | | (_| | |_) | |_) | |_| |
 |_|\__,_|_.__/|_.__/ \__, |
                      |___/
[/]
        """
    )
    return "=>"


def header(msg: str):
    console.print(
        Panel(f"[cyan]{msg}"),
        justify="center",
    )
    typer.echo("\n")


def provider_header(environment: str, provider: str, provider_version: str, msg: str):
    console.log(
        f"[cyan]Environment:[/] {environment}  [cyan]Provider:[/] {provider.upper()}"
        f"  [cyan]Version:[/] {provider_version}"
    )
    header(msg)


def flatten(data: MutableMapping[str, Any], parent_key="", sep=".") -> Dict[str, Any]:
    items: List = []
    for k, v in data.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for si in v:
                if isinstance(si, dict):
                    items.extend(flatten(si, new_key, sep=sep).items())
                else:
                    items.append((new_key, si))
        else:
            items.append((new_key, v))
    return dict(items)


def mergedicts(dict1: MutableMapping, dict2: MutableMapping):
    for key, value in dict2.items():
        if key in dict1:
            if isinstance(dict1[key], dict):
                if isinstance(value, dict):
                    mergedicts(dict1[key], value)
                else:
                    dict1[key] = value
            else:
                dict1[key] = value
        else:
            dict1[key] = value
    return dict1


def delete_nested_key(dicti, path):
    keys = path.split(".")
    keys_len = len(keys) - 1
    try:
        new_dict = {}
        for index, key in enumerate(keys):
            if index == keys_len:
                new_dict.pop(key)
                break
            if index == 0:
                new_dict = dicti[key]
            else:
                new_dict = new_dict[key]
        return dicti
    except KeyError as err:
        raise err


def dissect_url(target: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Takes URL and returns protocol, destination and resource.

    Example:
    >>> dissect_url("https://api.test.com/v2/resourceX")
    ("https", "api.test.com", "v2/resourceX")
    """
    match = re.search(
        r"((?P<protocol>\w+?)://)?(?P<destination>(\w+(-\w+)?\.?)+[a-z|0-9]+):?"
        r"(?P<port>\d+)?(/(?P<resource>[a-z]+\S+))?",
        target,
    )
    if match is None:
        raise ValueError(f"Could not dissect URL: {target}")
    return (
        match.groupdict().get("protocol"),
        match.groupdict().get("destination"),
        match.groupdict().get("resource"),
    )


def error_catcher(_func: Optional[Any] = None, parameter: Optional[str] = None):
    """Catches errors and exceptions and rich prints it."""
    def decorator_error_catcher(func):
        @functools.wraps(func)
        def wrapper_error_catcher(*args, **kwargs):
            try:
                # if parameter == "check_project":
                #     name = settings.SETTINGS.labby.project
                #     if name is None:
                #         console.print("[red]No project specified[/]")
                #         raise typer.Exit(code=1)
                value = func(*args, **kwargs)
                return value
            except typer.Exit:
                console.print("[red]Exiting...[/]\n")
            except Exception:
                console.print_exception()
        return wrapper_error_catcher

    if _func is None:
        return decorator_error_catcher
    else:
        return decorator_error_catcher(_func)


# def get_package_version() -> str:
#     data = settings.load_toml(Path(__file__).parent.parent / "pyproject.toml")
#     return data["tool"]["poetry"]["version"]
