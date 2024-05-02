#####################
Neutron Configuration
#####################

Neutron, the network service for OpenStack, supports a variety of
configurations to optimize and tailor network performance. This includes
integrating hardware acceleration technologies to enhance networking
capabilities within your OpenStack environment.

*********************
Hardware Acceleration
*********************

Hardware acceleration can significantly improve network performance by
offloading specific network functions to directly to the network interface
card (NIC). This reduces the load on the host CPU and improves network
throughput and latency.

ML2/OVS
=======

Mellanox Accelerated Switching And Packet Processing (ASAP\ :sup:`2`)
---------------------------------------------------------------------

Mellanox ASAP\ :sup:`2` is a technology that enables the offloading of the Open vSwitch
datapath to the NIC. This offloading is done by the NIC's firmware, and is
transparent to the host.

Atmosphere uses the `netoffload <https://github.com/vexxhost/netoffload>`_
project which takes care of validating and preparing the host for SR-IOV.

It is recommended to follow the ``netoffload`` `BIOS, Kernel & NIC configuration <https://github.com/vexxhost/netoffload#bios-configuration>`_
steps documented before getting started.

Open vSwitch configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to enable hardware off-loading in Open vSwitch, you must make sure that
you deploy with the following configuration:

.. code-block:: yaml

    openvswitch_helm_values:
      conf:
        ovs_hw_offload:
          enabled: true

Neutron configuration
^^^^^^^^^^^^^^^^^^^^^

In order to enable hardware off-loading in Neutron, you can simply deploy it
with the following configuration and it will use `netoffload <https://github.com/vexxhost/netoffload>`_
to automatically configure ASAP\ :sup:`2`.

.. admonition:: About ``Init`` errors
    :class: info

    If you see an Init error when deploying Neutron, you may need to look at the
    logs of the ``netoffload`` container to see what went wrong.

.. code-block:: yaml

    neutron_helm_values:
      conf:
        netoffload:
          asap2:
            - dev: enp97s0f0
              vfs: 16

ML2/OVN
=======

DPDK for provider & tenant networks
-----------------------------------

DPDK is a set of libraries and drivers for fast packet processing. It is
designed to run mostly in userspace, and can be used to accelerate network
functions in OpenStack.

DPDK can be used with OVN to accelerate the processing of packets in the
datapath. This can be done by enabling the DPDK support in the OVN
configuration.

Open vSwitch configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to enable hardware off-loading in Open vSwitch, you must make sure that
you deploy with the following configuration:

.. code-block:: yaml

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

For more details about configuring `socket_memory`, `lcore_mask`, and `driver`
parameters, please refer to the `OpenvSwitch documentation <https://docs.openvswitch.org/en/latest/intro/install/dpdk/#setup-ovs>`_.

OVN configuration
^^^^^^^^^^^^^^^^^

In order to enable hardware off-loading in OVN, you must make sure that
you deploy with the following configuration:

.. code-block:: yaml

    ovn_helm_values:
      network:
        interface:
          tunnel: br-ex
          tunnel_network_cidr: 192.168.0.0/19
      conf:
        ovn_bridge_mappings: external:br-ex
        ovn_bridge_datapath_type: netdev

Neutron configuration
^^^^^^^^^^^^^^^^^^^^^

In order to enable hardware off-loading in Neutron, you can simply deploy it
with the following configuration and it will take care of creating the
DPDK interfaces for you.

.. code-block:: yaml

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

Flavor configuration
^^^^^^^^^^^^^^^^^^^^

In order to use DPDK with OVN, you must create a flavor that supports DPDKw
which also includes making changes for the services that use the service
virtual machine model such as Octavia and Manila.

.. code-block:: yaml

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

    manila_flavor_extra_specs:
      "hw:vif_multiqueue_enabled": 'true'
      "hw:mem_page_size": large

    octavia_amphora_flavor_extra_specs:
      "hw:vif_multiqueue_enabled": 'true'
      "hw:mem_page_size": large
