# Neutron

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

## OVN with DPDK enabled provider and internal tunnel network traffic

To enable this configuration it is recommended to have the management interface separate
from the interfaces used with DPDK.  Additionally, you need to allocate enough 1g
huge memory pages for the interfaces and VMs' memory that will use this network. A
sample inventory with all the elements for DPDK enabled OVN configuration is below.
The example is using Mellanox NIC cards with the mlx5_core driver.

```yaml

# Add if manila or octavia VMs will be using the DPDK network
manila_flavor_extra_specs:
  "hw:vif_multiqueue_enabled": 'true'
  "hw:mem_page_size": large

octavia_amphora_flavor_extra_specs:
  "hw:vif_multiqueue_enabled": 'true'
  "hw:mem_page_size": large

# Here are some examples of internal and provider networks using the DPDK network
neutron_networks:
- external: true
  mtu_size: 1500
  name: dpdk-network
  port_security_enabled: true
  provider_network_type: vlan
  provider_segmentation_id: 999
  provider_physical_network: external
  shared: true
  subnets:
  - allocation_pool_start: 10.0.1.2
    allocation_pool_end: 10.0.1.254
    cidr: 10.0.10/24
    dns_nameservers:
      - 8.8.8.8
      - 8.8.8.8
    enable_dhcp: true
    gateway_ip: 10.0.1.1
    name: dpdk-network-subnet
- external: false
  mtu_size: 9000
  name: internal
  port_security_enabled: true
  shared: true
  subnets:
  - allocation_pool_start: 192.168.77.2
    allocation_pool_end: 192.168.77.254
    cidr: 192.168.77.0/24
    dns_nameservers:
      - 1.1.1.1
      - 1.1.1.1
    enable_dhcp: true
    gateway_ip: 192.168.77.1
    name: internal-subnet

# Socket_memory, lcore_mask, and driver parameters are depending on the environment
# See this OpenvSwitch [doc](https://docs.openvswitch.org/en/latest/intro/install/dpdk/#setup-ovs)
# for more information about tuning OpenvSwitch
openvswitch_helm_values:
  conf:
    ovs_dpdk:
      enabled: true
      socket_memory: 2048
      hugepages_mountpath: /dev/hugepages
      vhostuser_socket_dir: vhostuser
      lcore_mask: 0x1
      driver: mlx5_core
      vhost_iommu_support: true

# In these values we are defining the provider interface the same as our internal
# tunnel interface.  It assumes that the primary interface is for tunnel traffic and
# provider networks via VLAN.
ovn_helm_values:
  network:
    interface:
      tunnel: br-ex
      tunnel_network_cidr: 192.168.0.0/19
  conf:
    ovn_bridge_mappings: external:br-ex
    ovn_bridge_datapath_type: netdev

neutron_helm_values:
  conf:
    neutron:
      DEFAULT:
        global_physnet_mtu: 9100
    plugins:
      ml2_conf:
        ml2:
          path_mtu: 9100
          physical_network_mtus: external:9100
        ml2_type_vxlan:
          vni_ranges: 2000:1000000
    ovs_dpdk:
      enabled: true
      update_dpdk_bond_config: true
      driver: mlx5_core
      bonds:
        - name: dpdkbond
          bridge: br-ex
          migrate_ip: true
          mtu: 9100
          n_rxq: 2
          n_txq: 2
          n_rxq_size: 2048
          n_txq_size: 2048
          vhost_iommu_support: true
          ovs_options: 'bond_mode=balance-tcp lacp=active bond_updelay=10 bond_downdelay=10 other_config:lacp-time=fast'
          nics:
            - name: dpdk_b0s0
              pci_id: '0000:c1:00.0'
            - name: dpdk_b0s1
              pci_id: '0000:c1:00.1'
      modules:
        - name: dpdk
          log_level: info
      nics: null

# for any flavors that need to use a DPDK enabled network the extra_specs are require.
nova_flavors:
  - disk: 1
    name: m1.tiny
    ram: 512
    vcpus: 1
    extra_specs:
      "hw:vif_multiqueue_enabled": 'true'
      "hw:mem_page_size": 'large'
  - disk: 20
    name: m1.small
    ram: 2048
    vcpus: 1
    extra_specs:
      "hw:vif_multiqueue_enabled": 'true'
      "hw:mem_page_size": 'large'
```
