# Build Network Labs

- [Build Network Labs](#build-network-labs)
  - [Overview](#overview)
  - [Labby Project file](#labby-project-file)
  - [Topology phase](#topology-phase)
  - [Bootstrap phase](#bootstrap-phase)
  - [Configs phase](#configs-phase)
  - [Run all at once](#run-all-at-once)

## Overview

The purpose of the `labby build` command is to manage entire network topologies in a declarative way.

It has multiple phases which are divided into subcommands:

```shell
❯ labby build --help


  _       _     _
 | | __ _| |__ | |__  _   _
 | |/ _` | '_ \| '_ \| | | |
 | | (_| | |_) | |_) | |_| |
 |_|\__,_|_.__/|_.__/ \__, |
                      |___/  v0.2.0


Usage: labby build [OPTIONS] COMMAND [ARGS]...

  Builds a complete Network Provider Lab in a declarative way.

Options:
  --help  Show this message and exit.

Commands:
  bootstrap  Runs the bootstrap config process on the devices of a Project.
  configs    Runs the configuration process on the devices of a Project.
  project    Builds a Project in a declarative way.
  topology   Builds a Project Topology.
```

But first lets dive into the structure of the `labby_project.yml` file.

## Labby Project file

It is the declaration of the nodes specification, links setup and configuration, variables used to render post-bootstrap configuration (like OSPF or BGP variables) and main setting of the project (like `mgmt_network` and `template` configuration path).

The following shows an example `labby_project.yml` file and explains each section and relevant settings:

```yaml
---
# Main metadata section
main:
  name: lab-example
  description: Lab example
  contributors: ["David Flores <@davidban77>"]
  version: "0.0.1"
  labels: ["branch", "edge"]
  # Path of the post-bootstrap template for configuration provissioning of the nodes
  template: "./templates/main.j2"
  # Mgmt network settings
  mgmt_network:
    # Network to reach the devices
    network: 192.168.0.0/24
    gateway: 192.168.0.1/24
    # (Optional) IP Range available addresses to choose from for the network mgmt interfaces
    ip_range: [192.168.0.177, 192.168.0.190]
  # Mgmt network creds
  mgmt_creds:
    user: "netops"
    password: "netops123"

# Nodes specifications
nodes_spec:
  # It is template-based to reuse node specifications
  - template: "Cisco IOS CSR1kv 17.3.1a"
    nodes: ["csr-r1", "csr-r2"]
    net_os: "cisco_ios"
    # mgmt_port is a must have attribute
    mgmt_port: "Gi1"

  # Cloud and mgmt_switch are needed to enable external connectivity, so labby can reach it for provissioning.
  - template: "Cloud"
    nodes: ["cloud"]
    # These objects are builtin in GNS3 and NOT managed by labby.
    net_os: "builtin"
    config_managed: false
    labels: ["mgmt"]

  - template: "Ethernet switch"
    nodes: ["mgmt_switch"]
    net_os: "builtin"
    config_managed: false
    labels: ["mgmt"]

# Links specifications
links_spec:
  # It is node-based to reuse the link specifications
  - node: "mgmt_switch"
    links:
      - { "port": "Ethernet0", "node_b": "cloud", "port_b": "eth0" }
      - { "port": "Ethernet1", "node_b": "csr-r1", "port_b": "Gi1" }
      - { "port": "Ethernet2", "node_b": "csr-r2", "port_b": "Gi1" }
  - node: "csr-r1"
    links:
      - { "port": "Gi2", "node_b": "csr-r2", "port_b": "Gi2" }
      # In GNS3 You can assign filters in links to apply packet loss for exampel
      - {
          "port": "Gi3",
          "node_b": "csr-r2",
          "port_b": "Gi3",
          "filter": { "packet_loss": 50 },
        }

# Variables section used for post-bootstrap configuration provissioning
vars:
  # Global / default vars
  defaults:
    domain: "lab.local"

  # Group vars
  groups:
    global:
      snmp:
        communities:
          - community: public
            action: ro
        location: global

      syslog:
        default_level: info
        server: 172.29.160.50
        port: 7014
        protocol: udp

  # Host vars
  hosts:
    # You can assign hosts to a group
    csr-r1:
      group: global

      interfaces:
        - name: "Gi2"
          description: "OK channel"
          ipv4_address: 172.22.0.1/25
          enabled: true
          ospf:
            process: 77
            area: 0
            network_type: point-to-point

        - name: "Gi3"
          description: "Packet loss channel"
          ipv4_address: 172.23.0.1/25
          enabled: true
          ospf:
            process: 77
            area: 0
            network_type: point-to-point

        - name: "Loopback0"
          ipv4_address: 172.22.77.1/32
          ospf:
            process: 77
            area: 0

      ospf:
        process: 77
        router_id: "172.22.77.1"

    csr-r2:
      group: global

      interfaces:
        - name: "Gi2"
          description: "OK channel"
          ipv4_address: 172.22.0.2/25
          enabled: true
          ospf:
            process: 77
            area: 0
            network_type: point-to-point

        - name: "Gi3"
          description: "Packet loss channel"
          ipv4_address: 172.23.0.2/25
          enabled: true
          ospf:
            process: 77
            area: 0
            network_type: point-to-point

        - name: "Loopback0"
          ipv4_address: 172.22.77.2/32
          ospf:
            process: 77
            area: 0

      ospf:
        process: 77
        router_id: "172.22.77.2"
```

---

## Topology phase

The topology phase is in charge of creating the network project, the nodes and its links.

This is basically a wrapper around commads like:

- `labby create project`
- `labby create node`
- `labby create link`

To run the topology phase:

```shell
> labby build topology -f labby_project.yml
```

## Bootstrap phase

it is in charge of starting up the nodes and trying to run configuration dialogs and general device prompts to bootstrap the device with basic configuration in order to be reachable via SSH.

For the **bootstrap** provision process, it relies on `scrapli-telnet` in the case of GNS3, in order to connect to the device console connection.

To run the bootstrap phase:

```shell
> labby build bootstrap -f labby_project.yml
```

Unfourtunately the entire bootstrap process is not entirely predictable, sometimes the configuration dialogs prompts differ from version to version, or the initial bootstrap interaction process differs as well. So as an alternative we provide the means to render the bootstrap configuration to be able to copy/paste it.

```shell
# Render the bootstrap configuration to stdout
> labby run node bootstrap csr-r1 --project lab-example --render

# You can copy and paste it later in a console connection (it needs telnet)
> labby connect node csr-r1 --project lab-example --console
```

## Configs phase

It is in charge of provisioning the device once SSH reachability configuration is good. It relies in `nornir` to configure the instances.

This phase relies on the `vars` section of the `labby_project.yml` and the `templates` to render and provision network device configuration. You can see an example of the templates in the [examples section](../example/bgp-example/templates).

To run the configuration phase:

```shell
> labby build configs -f labby_project.yml
```

## Run all at once

Now, you can run the entire provision process in one go with the following command:

```shell
> labby build project -f labby_project.yml
```

This is interactive, meaning that it will prompt you to continue or skip a phase. This is particularly useful if you have issues with the bootstrap process and you want to do it in another way.
