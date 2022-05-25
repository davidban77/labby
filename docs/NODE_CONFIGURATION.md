# Node Configuration Management

The **nodes** can be configured and provissioned with `labby`.

## Bootstrap Configuration

A bootstrap configuration is referred to the initial configuration needed on a device or **node** to be able to access it remotely.

The configuration is usually composed of basic user settings for SSH access and Management interface and IP address configuration.

The configuration can be rendered... (*insert feature here*)

There is a command `labby run node bootstrap` that interacts with this configuration and tries to push it to a target node using its console connection. In the case of GNS3 this usually done via `telnet` on a specific port of the GNS3 server.

## Configuration rendering and push

Labby also has a way to render and push a configuration based on `template` and `variable` file.

In the [example node-config folder](../example/node_config/) you can see an `interface.conf.j2` template and a couple of variable files (one for the node `eos-r1.yml` and another one for `ios-r1.yml`).

The following command lets you push the configuration over their SSH connetion:

```shell
labby run node config eos-r1 --project labby-test --user netops --template ./example/node_config/interface.conf.j2 --vars ./example/node_config/eos-r1.yml
```

For this to work there are a couple of requirements:

- Labby `node` created and configured with a reachable Management IP address for SSH traffic.
- User `netops` configured and with enough permissions to add new configuration on it.

> **Note**
> For GNS3, in order to have external connectivity on the management interface you will usually create a management builtin switch (Ethernet Switch) connect the network device mgmt port to it, and also create cloud object and connect it to it. Also make sure that the IP Addresses are routeble/reachable.

### Configuration over console

Labby configures the device over console as well!, it just needs to have the right prompt the device terminal(usually `#`).

So, we can run the previous command by just adding the `--console` flag:

```shell
labby run node config eos-r1 --project labby-test --user netops --template ./example/node_config/interface.conf.j2 --vars ./example/node_config/eos-r1.yml --console
```

## Full Project configuration

TBC
