######
Ironic
######

***********************************************************
Make Neutron aware of bare metal physical network topology
***********************************************************

.. note::

   This feature requires an environment with the Neutron Ironic agent.
   `Atmosphere PR 3925 <https://github.com/vexxhost/atmosphere/pull/3925>`__
   adds support for enabling that agent through
   ``neutron_helm_values.manifests.deployment_ironic_agent``.

Atmosphere can enable the Neutron Ironic agent together with the Neutron
``baremetal`` backend so Neutron can understand the physical network topology
of Ironic bare metal nodes.

The Neutron Ironic agent reports Ironic bare metal port and physical network
information to Neutron. The ``baremetal`` backend lets the ML2 binding flow use
that information when it binds Neutron ports with ``vnic_type=baremetal``.
Neutron needs both parts to place bare metal ports on the correct provider or
routed provider network segment.

Bare metal networking lets virtual machines and Ironic bare metal nodes use the
same provider network. This is useful when a workload needs direct network
communication between virtual machine instances and bare metal instances.

.. warning::

   This currently works only in OVN environments. The Neutron network used for
   virtual machine to bare metal traffic must not use security groups.

Create the Neutron network without port security:

.. code-block:: console

   openstack network create bm-network \
     --provider-network-type vlan \
     --provider-physical-network external \
     --provider-segment 200 \
     --disable-port-security

For an existing network, disable port security before you use it for bare metal
traffic:

.. code-block:: console

   openstack network set bm-network --disable-port-security

When you create the Neutron port for the bare metal instance, request the bare
metal port binding type:

.. code-block:: console

   openstack port create baremetal-port \
     --network bm-network \
     --vnic-type baremetal

Use the Neutron port when you create the bare metal server:

.. code-block:: console

   openstack server create bm-server \
     --flavor baremetal \
     --image baremetal-image \
     --port baremetal-port

The Ironic bare metal port must also include the physical network name that
matches the Neutron provider network. For the default external provider
network, set ``external`` on the Ironic bare metal port:

.. code-block:: console

   openstack baremetal port set <port> --physical-network external

You can verify the value with:

.. code-block:: console

   openstack baremetal port list --long \
     -c UUID -c "Node UUID" -c "Physical Network"

If the deployment uses another physical network name, use that name instead of
``external``. Ports without the matching physical network can fail to bind to
the provider network.
