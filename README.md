# Labby

![CI](https://github.com/davidban77/labby/actions/workflows/ci.yml/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
<!-- [![codecov](https://codecov.io/gh/davidban77/labby/branch/develop/graph/badge.svg)](https://codecov.io/gh/davidban77/labby) -->
<!-- [![Total alerts](https://img.shields.io/lgtm/alerts/g/davidban77/labby.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/davidban77/labby/alerts/) -->
<!-- [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/davidban77/labby.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/davidban77/labby/context:python) -->
[![pypi](https://img.shields.io/pypi/v/labby.svg)](https://pypi.python.org/pypi/labby)
[![versions](https://img.shields.io/pypi/pyversions/labby.svg)](https://github.com/davidban77/labby)

CLI Tool for interacting with Network Virtualization systems to build and interact with Network Labs in an automated way.

## Documentation

<Warning>

*TBD*

</Warning>

## Providers

`labby` relies on *`providers`* to interact, create and destroy with the Network Topologies. The provider supported so far is **GNS3** by the use of [`gns3fy`](https://github.com/davidban77/gns3fy).

## Install

It is as simple as

```shell
pip install labby
```

### Developer version

You will need to use `poetry` to handle installation and dependencies.

```shell
# Clone the repository
git clone https://github.com/davidban77/labby.git
cd labby

# Start poetry shell and install the dependencies
poetry shell
poetry install
```

---

## How it works

The CLI tool serves multiple purposes, for example it is a way great to discover the projects or network topologies avaiable on the Network Virtualization system, start or stop the nodes, push configuration, etc...

For examplem to show the available projects and their status in GNS3:

![Projects lists](imgs/labby_projects_lists.png)

Now, let's get the details of the network lab `topology-01`:

![Project Detail](imgs/labby_project_detail.png)

It is a small topology with 2 Arista `ceos` devices connected between each other, and also connected to a `cloud` and `mgmt` switch to allow them to be reachable to the outside world.

The **Mgmt Address** shows the IP address information for their management interfaces. The setup and configuration of those are explained in the *Docs*.

You can start the nodes of the entire project one by one, for example:

![Start Project](imgs/labby_start_project.png)

Devices are up and you can check their status and more details:

![Node Detail](imgs/labby_node_detail.png)

You can connect to the nodes via SSH (if IP address for management is set and is reachable), or you can connect over console if available. For example:

![Connect Router](imgs/labby_connect_router.png)

And like this there are many more features...
