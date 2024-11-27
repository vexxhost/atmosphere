==========
Bare-metal
==========

In general, an Atmosphere deployment starts with a fleet of bare metal servers
with a base OS installed.  From there, the Atmosphere deployment process will
install Ceph, Kubernetes, and OpenStack on top of the base OS.  The current
supported base operating systems are:

- Ubuntu 20.04 LTS
- Ubuntu 22.04 LTS (**recommended**)
- Rocky Linux 9

**********
Networking
**********

The recommended approach for networking on the hosts that will be used by the
Atmosphere deployment is to have the following networks:

Management network
  This network will be used for all inter-cloud communication between the
  different components of the Atmosphere deployment.  Examples of traffic
  that goes across the management network includes:  OpenStack API traffic
  (tunneled over Geneve through Cilium), Ceph cluster & replication traffic,
  VXLAN (for ML2/OVS) or Geneve (for ML2/OVN) tunnel traffic

External (provider) network
  This network will be used for all external traffic to the cloud workloads,
  such as the floating IPs or directly connected workloads.  This network
  should be routable from the outside world.
  
  It could be a public network such as the internet or a private "intranet"
  network and you can have multiple external networks if you want to segregate traffic.

Host Configuration
==================

The hosts can be configured in a variety of different supported schemes depending
on the number of network interfaces available on the host.

.. admonition:: LACP
  
    It is recommended to use LACP (Link Aggregation Control Protocol) to bond
    multiple network interfaces together to provide redundancy and increased
    bandwidth.  This is especially important for the management network.

In general, all of the network interfaces on all the hosts should be configured
identically.  The only exception is that the storage nodes do not require the
external network to be configured since they do not need to communicate with
the external network.

Single NIC/Bond
---------------

If you have a single NIC or a single bond, it is recommended that you configure
the management network on a tagged VLAN on the NIC/bond and leave the external/provider
network untagged.

This will allow you to add the untagged NIC interface to the external network
bridge in the OpenStack deployment while the tagged VLAN interface will be used
for the management network.

Dual NIC/Bond
-------------

If you have two NICs or two bonds, it is recommended that you configure the
management network on one NIC/bond and the external/provider network on the
other NIC/bond.

In this case, you do not need to use VLANs for the management network as it
will be on a separate NIC/bond from the external network so you can use the
untagged interface for the management network.
