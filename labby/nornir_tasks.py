from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
from nornir.core.task import Task
from nornir_scrapli.tasks import send_config, send_command
from nornir.core.helpers.jinja_helper import render_from_file
from labby.models import LabbyProject
from labby import utils

if TYPE_CHECKING:
    from labby.project_data import ProjectData


SHOW_RUN_COMMANDS = {
    "arista_eos": "show run",
    "cisco_ios": "show run",
    "cisco_iosxe": "show run",
    "cisco_nxos": "show run",
}


SAVE_COMMANDS = {
    "arista_eos": "wr mem",
    "cisco_ios": "wr mem",
    "cisco_iosxe": "wr mem",
    "cisco_nxos": "copy running-config startup-config",
}


def backup_task(task: Task):
    task.run(task=send_command, command=SHOW_RUN_COMMANDS[task.host.platform])  # type: ignore


def save_task(task: Task):
    task.run(task=send_command, command=SAVE_COMMANDS[task.host.platform])  # type: ignore


def config_task(task: Task, project_data: ProjectData, project: LabbyProject):
    cfg_data = render_from_file(
        path=str(Path(project_data.template).parent),
        template=Path(project_data.template).name,
        jinja_filters={"ipaddr": utils.ipaddr_renderer},
        **dict(project=project, node=task.host.data["labby_obj"], **project_data.vars),
    )
    task.run(task=send_config, config=cfg_data)
