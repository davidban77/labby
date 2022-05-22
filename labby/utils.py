"""Utility module for Labby."""
import re
from typing import Dict, List, Any, MutableMapping, Tuple, Optional, Literal

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from netaddr import IPNetwork

from labby import __version__


IpAddressFilter = Literal["address", "netmask"]


custom_theme = Theme({"warning": "bold magenta", "error": "bold red", "good": "bold green"})


console = Console(color_system="auto", log_path=False, record=True, theme=custom_theme)


def banner():
    # pylint: disable=anomalous-backslash-in-string
    """A function to print out the banner for labby to the terminal."""
    console.print(
        f"""
[green]
  _       _     _
 | | __ _| |__ | |__  _   _
 | |/ _` | '_ \| '_ \| | | |
 | | (_| | |_) | |_) | |_| |
 |_|\__,_|_.__/|_.__/ \__, |
                      |___/  [bold]v{__version__}[/bold]
[/green]
        """
    )
    return "=>"


def header(msg: str):
    """
    Prints a header to the terminal, for any given message.

    Args:
        msg (str): A message to use for the header.
    """
    console.print(
        Panel(f"[cyan]{msg}"),
        justify="center",
    )
    typer.echo("\n")


def provider_header(environment: str, provider: str, provider_version: str, msg: str):
    """
    Prints rich content to the terminal, and prints a header for any given message.

    Args:
        environment (str): The environment in which labby is working.
        provider (str): The name of the provider.
        provider_version (str): The version of the provider.
        msg (str): A message to use fr the header.
    """
    console.log(
        f"[cyan]Environment:[/] {environment}  [cyan]Provider:[/] {provider.upper()}"
        f"  [cyan]Version:[/] {provider_version}"
    )
    header(msg)


def flatten(data: MutableMapping[str, Any], parent_key="", sep=".") -> Dict[str, Any]:
    """
    A function to flatten a dictionary.

    Args:
        data (MutableMapping[str, Any]): Dictionary you wish to flatten.

    Returns:
        A new dictionary, with the elements of the original dictionary but flattened.
    """
    items: List = []
    for k, value in data.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(value, dict):
            items.extend(flatten(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            for sub_ins in value:
                if isinstance(sub_ins, dict):
                    items.extend(flatten(sub_ins, new_key, sep=sep).items())
                else:
                    items.append((new_key, sub_ins))
        else:
            items.append((new_key, value))
    return dict(items)


def mergedicts(dict1: MutableMapping, dict2: MutableMapping) -> MutableMapping[str, Any]:
    """
    A function to merge to dictionaries.

    Args:
        dict1 (MutableMapping): A dictionary different from dict2.
        dict2 (MutableMapping): A dictionary different from dict1.

    Returns:
        dict1 merged with dict2.
    """
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


def delete_nested_key(dicti: MutableMapping, path: str) -> MutableMapping[str, Any]:
    """
    Deletes a nested key from a dictionary.

    Args:
        dicti (MutableMapping): A dictionary
        path (str): Path of the key?

    Raises:
        KeyError: If key is not in dictionary.
    """
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


def load_yaml_file(path: str) -> Dict[str, Any]:
    """Loads YAML file."""
    with open(path, "r", encoding="utf-8") as fil:
        return yaml.safe_load(fil)


# TODO: Add logic to read possible encoded envvar from project file for network device creds
# or at least from environemt variable
def check_creds(user: str, password: str) -> bool:
    """Needs to be worked on."""
    # pylint: disable=unused-argument
    return True


def ipaddr_renderer(value: str, *, render: IpAddressFilter) -> str:
    """Renders an IP address related values.

    Args:
        value (str): IP address/prefix to render the information from.
        action (str, optional): Action to determine method to render. Defaults to "address".

    Returns:
        str: address value
    """
    to_render = ""
    if render == "address":
        to_render = str(IPNetwork(addr=value).ip)
    elif render == "netmask":
        to_render = str(IPNetwork(addr=value).netmask)
    else:
        raise ValueError()
    return to_render


# def get_package_version() -> str:
#     data = settings.load_toml(Path(__file__).parent.parent / "pyproject.toml")
#     return data["tool"]["poetry"]["version"]
