from typing import Optional


def bool_status(bool_value: Optional[bool]) -> str:
    """Returns the status for the bool."""
    if bool_value is True:
        value = "[cyan]Yes[/cyan]"
    elif bool_value is False:
        value = "[orange1]No[/orange1]"
    else:
        value = "None"
    return value


def string_status(str_value: str) -> str:
    """Returns the string status."""
    return "None" if str_value == "" else str_value


def node_status(status: Optional[str]) -> str:
    """Returns the status for a node."""
    STATUS_CODES = {
        "started": "[green]started[/]",
        "stopped": "[red]stopped[/]",
        "suspended": "[yellow]suspended[/]",
    }
    return STATUS_CODES[status] if status else "None"


def link_status(status: Optional[str]) -> str:
    """Returns the link status."""
    STATUS_CODES = {
        "present": "[green]present[/]",
        "deleted": "[red]deleted[/]",
        "suspended": "[yellow]suspended[/]",
    }
    return STATUS_CODES[status] if status else "None"


def node_net_os(net_os: Optional[str]) -> str:
    """Returns the net_os for a node."""
    NET_OS = {
        "cisco_ios": "[hot_pink3]cisco_ios[/]",
        "cisco_nxos": "[light_sea_green]cisco_nxos[/]",
        "cisco_xr": "[medium_purple2]cisco_xr[/]",
        "arista_eos": "[light_slate_blue]arista_eos[/]",
        "juniper_junos": "[dodger_blue3]juniper_junos[/]",
    }
    return NET_OS.get(net_os, f"[white]{net_os}[/]") if net_os else "None"


def template_type(t_type: Optional[str]) -> str:
    TEMPLATE_TYPE = {
        "qemu": "[rosy_brown]qemu[/]",
        "docker": "[bright_blue]docker[/]",
    }
    return TEMPLATE_TYPE.get(t_type, f"[white]{t_type}[/]") if t_type else "None"


def project_status(status: Optional[str]) -> str:
    """Returns the status for a project."""
    STATUS_CODES = {
        "opened": "[green]started[/]",
        "closed": "[red]stopped[/]",
    }
    return STATUS_CODES[status] if status else "None"
