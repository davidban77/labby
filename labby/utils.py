import typer
from typing import Dict, List, Any, MutableMapping
from rich.console import Console
from rich.panel import Panel


console = Console(color_system="auto", log_path=False, record=True)


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
