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

```shell
❯ labby get project list


  _       _     _
 | | __ _| |__ | |__  _   _
 | |/ _` | '_ \| '_ \| | | |
 | | (_| | |_) | |_) | |_| |
 |_|\__,_|_.__/|_.__/ \__, |
                      |___/  v0.1.0


[23:00:38]                                             GNS3 Projects
           ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
           ┃ Project Name     ┃ Status  ┃ Auto Start ┃ Auto Close ┃ Auto Open ┃ Labels                         ┃
           ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
           │ topology-01      │ stopped │ No         │ Yes        │ No        │ ['telemetry', 'observability'] │
           │ labby_test       │ stopped │ No         │ No         │ No        │ []                             │
           │ prefect-demo     │ stopped │ No         │ Yes        │ No        │ ['orchestration', 'flows']     │
           │ tpg-demo         │ stopped │ No         │ No         │ No        │ ['telemetry', 'test']          │
           │ branch-Dublin    │ stopped │ No         │ Yes        │ No        │ ['site', 'mpls']               │
           └──────────────────┴─────────┴────────────┴────────────┴───────────┴────────────────────────────────
```

Now, let's get the details of the network lab `topology-01`:

```shell
❯ labby get project detail topology-01


  _       _     _
 | | __ _| |__ | |__  _   _
 | |/ _` | '_ \| '_ \| | | |
 | | (_| | |_) | |_) | |_| |
 |_|\__,_|_.__/|_.__/ \__, |
                      |___/  v0.1.0


[23:05:44] (topology-01) Starting project
[23:05:47] (topology-01) Collecting project data
[23:05:49] (topology-01) Project started
           Project: topology-01
           ┏━━━━━━━━━┯━━━━━━━━┯━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
           ┃ Status  │ #Nodes │ #Links │ Labels                         │ Auto Start │ Auto Close │ Auto Open │ ID                                   ┃
           ┠─────────┼────────┼────────┼────────────────────────────────┼────────────┼────────────┼───────────┼──────────────────────────────────────┨
           ┃ started │ 4      │ 5      │ ['telemetry', 'observability'] │ No         │ Yes        │ No        │ 0cd7c82b-e44e-43db-835c-54b884d99e78 ┃
           ┗━━━━━━━━━┷━━━━━━━━┷━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

                                                                                      Nodes Information
           ┏━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
           ┃ Name        ┃ Status  ┃ Kind           ┃ Category ┃ NET OS     ┃ Model ┃ Version  ┃ Builtin ┃ Console Port ┃ Labels     ┃ Mgmt Address   ┃ Config Managed ┃ # Ports ┃
           ┡━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
           │ ceos-01     │ stopped │ qemu           │ switch   │ arista_eos │ veos  │ 4.25.0FX │ No      │ 5000         │ ['router'] │ 192.168.0.16/… │ Yes            │ 13      │
           ├─────────────┼─────────┼────────────────┼──────────┼────────────┼───────┼──────────┼─────────┼──────────────┼────────────┼────────────────┼────────────────┼─────────┤
           │ ceos-02     │ stopped │ qemu           │ switch   │ arista_eos │ veos  │ 4.25.0FX │ No      │ 5002         │ ['router'] │ 192.168.0.17/… │ Yes            │ 13      │
           ├─────────────┼─────────┼────────────────┼──────────┼────────────┼───────┼──────────┼─────────┼──────────────┼────────────┼────────────────┼────────────────┼─────────┤
           │ cloud       │ started │ cloud          │ guest    │ None       │ None  │ None     │ Yes     │ None         │ ['mgmt']   │ 192.168.0.18/… │ No             │ 2       │
           ├─────────────┼─────────┼────────────────┼──────────┼────────────┼───────┼──────────┼─────────┼──────────────┼────────────┼────────────────┼────────────────┼─────────┤
           │ mgmt-switch │ started │ ethernet_swit… │ switch   │ None       │ None  │ None     │ Yes     │ 5005         │ ['mgmt']   │ 192.168.0.19/… │ No             │ 8       │
           └─────────────┴─────────┴────────────────┴──────────┴────────────┴───────┴──────────┴─────────┴──────────────┴────────────┴────────────────┴────────────────┴─────────┘

                                                         Links Information
           ┏━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┓
           ┃ Node A      ┃ Port A    ┃ Node B  ┃ Port B      ┃ Status  ┃ Capturing ┃ Filters ┃ Labels       ┃ Kind     ┃
           ┡━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━┩
           │ mgmt-switch │ Ethernet0 │ cloud   │ eth0        │ present │ No        │ {}      │ ['mgmt_ext'] │ ethernet │
           ├─────────────┼───────────┼─────────┼─────────────┼─────────┼───────────┼─────────┼──────────────┼──────────┤
           │ mgmt-switch │ Ethernet1 │ ceos-01 │ Management1 │ present │ No        │ {}      │ []           │ ethernet │
           ├─────────────┼───────────┼─────────┼─────────────┼─────────┼───────────┼─────────┼──────────────┼──────────┤
           │ mgmt-switch │ Ethernet2 │ ceos-02 │ Management1 │ present │ No        │ {}      │ []           │ ethernet │
           ├─────────────┼───────────┼─────────┼─────────────┼─────────┼───────────┼─────────┼──────────────┼──────────┤
           │ ceos-01     │ Ethernet1 │ ceos-02 │ Ethernet1   │ present │ No        │ {}      │ []           │ ethernet │
           ├─────────────┼───────────┼─────────┼─────────────┼─────────┼───────────┼─────────┼──────────────┼──────────┤
           │ ceos-01     │ Ethernet2 │ ceos-02 │ Ethernet2   │ present │ No        │ {}      │ []           │ ethernet │
           └─────────────┴───────────┴─────────┴─────────────┴─────────┴───────────┴─────────┴──────────────┴──────────┘
           (topology-01) Stopping project
[23:05:52] (topology-01) Collecting project data
           (topology-01) Project stopped
```

It is a small topology with 2 Arista `ceos` devices connected between each other, and also connected to a `cloud` and `mgmt` switch to allow them to be reachable to the outside world.

The **Mgmt Address** shows the IP address information for their management interfaces. The setup and configuration of those are explained in the *Docs*.

You can start the nodes of the entire project one by one, for example:

```shell
❯ labby start project topology-01 --start-nodes one_by_one


  _       _     _
 | | __ _| |__ | |__  _   _
 | |/ _` | '_ \| '_ \| | | |
 | | (_| | |_) | |_) | |_| |
 |_|\__,_|_.__/|_.__/ \__, |
                      |___/  v0.1.0


[23:12:26] (topology-01) Starting project
[23:12:28] (topology-01) Collecting project data
[23:12:30] (topology-01) Project started
           Project: topology-01
           ┏━━━━━━━━━┯━━━━━━━━┯━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
           ┃ Status  │ #Nodes │ #Links │ Labels                         │ Auto Start │ Auto Close │ Auto Open │ ID                                   ┃
           ┠─────────┼────────┼────────┼────────────────────────────────┼────────────┼────────────┼───────────┼──────────────────────────────────────┨
           ┃ started │ 4      │ 5      │ ['telemetry', 'observability'] │ No         │ Yes        │ No        │ 0cd7c82b-e44e-43db-835c-54b884d99e78 ┃
           ┗━━━━━━━━━┷━━━━━━━━┷━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
           (topology-01) Starting project
[23:12:32] (topology-01)(ceos-01) Starting node
[23:12:35] (topology-01)(ceos-01) Collecting node data
           (topology-01)(ceos-01) Node started
[23:12:45] (topology-01)(ceos-02) Starting node
[23:12:47] (topology-01)(ceos-02) Collecting node data
[23:12:48] (topology-01)(ceos-02) Node started
▰▰▰▰▰▱▱ (topology-01)(ceos-02) Waiting for node warmup: ceos-02
[23:12:58] (topology-01)(cloud) Node already started...
           (topology-01)(mgmt-switch) Node already started...
           (topology-01) Project nodes have been started
           (topology-01) Collecting project data
[23:12:59] (topology-01) Project started
```

Devices are up and you can check their status and more details:

```shell
❯ labby get node detail -p topology-01 ceos-01


  _       _     _
 | | __ _| |__ | |__  _   _
 | |/ _` | '_ \| '_ \| | | |
 | | (_| | |_) | |_) | |_| |
 |_|\__,_|_.__/|_.__/ \__, |
                      |___/  v0.1.0


[23:16:40] (topology-01) Collecting project data
[23:16:42] Project: topology-01
           ┏━━━━━━━━━┯━━━━━━━━┯━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
           ┃ Status  │ #Nodes │ #Links │ Labels                         │ Auto Start │ Auto Close │ Auto Open │ ID                                   ┃
           ┠─────────┼────────┼────────┼────────────────────────────────┼────────────┼────────────┼───────────┼──────────────────────────────────────┨
           ┃ started │ 4      │ 5      │ ['telemetry', 'observability'] │ No         │ Yes        │ No        │ 0cd7c82b-e44e-43db-835c-54b884d99e78 ┃
           ┗━━━━━━━━━┷━━━━━━━━┷━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
           (topology-01) Collecting project data
           Node: ceos-01
           ┏━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
           ┃ Attributes     │ Value                                ┃
           ┠────────────────┼──────────────────────────────────────┨
           ┃ id             │ b3927785-39b3-4a5c-abbe-01befdd06f89 ┃
           ┃ template       │ Arista EOS vEOS 4.25.0FX             ┃
           ┃ kind           │ qemu                                 ┃
           ┃ project        │ topology-01                          ┃
           ┃ status         │ started                              ┃
           ┃ console        │ 5000                                 ┃
           ┃ category       │ switch                               ┃
           ┃ net_os         │ arista_eos                           ┃
           ┃ model          │ veos                                 ┃
           ┃ version        │ 4.25.0FX                             ┃
           ┃ #Ports         │ 13                                   ┃
           ┃ labels         │ ['router']                           ┃
           ┃ mgmt_addr      │ 192.168.0.16/24                      ┃
           ┃ mgmt_port      │ Management1                          ┃
           ┃ config_managed │ True                                 ┃
           ┗━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

           ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Ports ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
           ┃ Management1, Ethernet1, Ethernet2, Ethernet3, Ethernet4, Ethernet5, Ethernet6, Ethernet7, Ethernet8, Ethernet9, Ethernet10, Ethernet11, Ethernet12 ┃
           ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

           ┏━━━━━━━━━━━━━━━━━━━━━━ Links ━━━━━━━━━━━━━━━━━━━━━━━┓
           ┃ ╭─────────────────── Link: 0 ────────────────────╮ ┃
           ┃ │ ceos-01: Ethernet2 == ceos-02: Ethernet2       │ ┃
           ┃ ╰────────────────────────────────────────────────╯ ┃
           ┃ ╭─────────────────── Link: 1 ────────────────────╮ ┃
           ┃ │ ceos-01: Ethernet1 == ceos-02: Ethernet1       │ ┃
           ┃ ╰────────────────────────────────────────────────╯ ┃
           ┃ ╭─────────────────── Link: 2 ────────────────────╮ ┃
           ┃ │ mgmt-switch: Ethernet1 == ceos-01: Management1 │ ┃
           ┃ ╰────────────────────────────────────────────────╯ ┃
           ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

You can connect to the nodes via SSH (if IP address for management is set and is reachable), or you can connect over console if available. For example:

```shell
❯ labby connect node -p topology-01 -u netops ceos-01


  _       _     _
 | | __ _| |__ | |__  _   _
 | |/ _` | '_ \| '_ \| | | |
 | | (_| | |_) | |_) | |_| |
 |_|\__,_|_.__/|_.__/ \__, |
                      |___/  v0.1.0


[23:19:15] (topology-01) Collecting project data
[23:19:16] Project: topology-01
           ┏━━━━━━━━━┯━━━━━━━━┯━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
           ┃ Status  │ #Nodes │ #Links │ Labels                         │ Auto Start │ Auto Close │ Auto Open │ ID                                   ┃
           ┠─────────┼────────┼────────┼────────────────────────────────┼────────────┼────────────┼───────────┼──────────────────────────────────────┨
           ┃ started │ 4      │ 5      │ ['telemetry', 'observability'] │ No         │ Yes        │ No        │ 0cd7c82b-e44e-43db-835c-54b884d99e78 ┃
           ┗━━━━━━━━━┷━━━━━━━━┷━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
           (topology-01) Collecting project data
Warning: Permanently added '192.168.0.16' (ED25519) to the list of known hosts.
(netops@192.168.0.16) Password:
Last login: Sun May 22 22:19:06 2022 from 192.168.0.109
ceos-01>en
ceos-01#show ip int br
                                                                               Address
Interface         IP Address            Status       Protocol           MTU    Owner
----------------- --------------------- ------------ -------------- ---------- -------
Management1       192.168.0.16/24       up           up                1500

ceos-01#exit
Connection to 192.168.0.16 closed.
```

And like this there are many more features...
