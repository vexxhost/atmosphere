# Networking

## Hardware Acceleration

### Mellanox Accelerated Switching And Packet Processing (ASAP2)

Mellanox ASAP2 is a technology that enables the offloading of the Open vSwitch
datapath to the NIC. This offloading is done by the NIC's firmware, and is
transparent to the host.

Atmosphere uses the [`netoffload`](https://github.com/vexxhost/netoffload)
project which takes care of validating and preparing the host for SR-IOV.

It is recommended to follow the BIOS, Kernel & NIC configuration steps documented
within the [`netoffload`](https://github.com/vexxhost/netoffload#bios-configuration)
project before getting started.

#### Open vSwitch configuration

In order to enable hardware off-loading in Open vSwitch, you must make sure that
you deploy with the following configuration:

```yaml
openvswitch_helm_values:
  conf:
    ovs_hw_offload:
      enabled: true
```

#### Neutron configuration

In order to enable hardware off-loading in Neutron, you can simply deploy it
with the following configuration and it will use
[`netoffload`](https://github.com/vexxhost/netoffload) to automatically
configure ASAP2.

!!! note

    If you see an Init error when deploying Neutron, you may need to look at the
    logs of the `netoffload` container to see what went wrong.

```yaml
neutron_helm_values:
  conf:
    netoffload:
      asap2:
        - dev: enp97s0f0
          vfs: 16
```
