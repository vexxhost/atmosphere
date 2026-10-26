#############################
Bare metal graphical consoles
#############################

Atmosphere gives bare metal nodes the same browser-based graphical console
that virtual machines have, and turns it on whenever Ironic is deployed. When
a console is opened, the Ironic conductor starts a short-lived Pod that signs
in to the node's BMC web console and serves it over VNC. ``ironic-novncproxy``
and ``nova-novncproxy`` carry that session to the browser.

The console image supports Dell iDRAC, HPE iLO and Supermicro BMCs over
Redfish.

.. note::

    For more details about how Ironic implements graphical consoles, refer to
    the `Ironic graphical console documentation
    <https://docs.openstack.org/ironic/latest/install/graphical-console.html>`_.

Requirements
============

- Ironic and Nova from the OpenStack 2026.1 release or later. Ironic added the
  Kubernetes console provider in 2026.1, and Nova added VNC consoles for bare
  metal instances in the same release.
- A DNS record for the console hostname. It defaults to the Ironic API
  hostname with its first label replaced by ``baremetal-console``, so an API at
  ``baremetal.cloud.example.com`` gets a console at
  ``baremetal-console.cloud.example.com``. Set
  ``openstack_helm_endpoints_ironic_novnc_host`` to use a different name.

What Atmosphere deploys
=======================

Alongside Ironic, Atmosphere deploys:

- ``ironic-novncproxy`` behind its own Ingress on the console hostname,
- the ``openstack-ironic-vnc`` namespace, where the Ironic conductor creates a
  console Pod and a Secret holding the BMC credentials for each open console,
- a NetworkPolicy that lets only ``ironic-novncproxy`` and ``nova-novncproxy``
  reach the console Pods, because their VNC servers have no encryption or
  authentication.

The console Ingress takes its class and annotations from
``ironic_novnc_ingress_class_name`` and ``ironic_novnc_ingress_annotations``,
the same way the Nova console Ingress does.

Open a console on a node
========================

New nodes that use the ``redfish`` hardware type get the
``redfish-graphical`` console interface automatically. Nodes enrolled before
consoles were available keep their existing interface, so switch them once:

.. code-block:: console

 $ openstack baremetal node set $NODE --console-interface redfish-graphical

Then enable the console and get its URL:

.. code-block:: console

 $ openstack baremetal node console enable $NODE
 $ openstack baremetal node console show $NODE

In the examples above, ``$NODE`` is the name or UUID of the bare metal node.
Disable the console when you're done, which stops its Pod:

.. code-block:: console

 $ openstack baremetal node console disable $NODE

Open a console on a bare metal instance
=======================================

Users reach consoles for their bare metal instances through Nova, the same way
they do for virtual machines. Nova needs ``nova-compute-ironic``, which is not
deployed by default. Enable it with:

.. code-block:: yaml

    nova_helm_values:
      manifests:
        statefulset_compute_ironic: true

Users can then get a console URL for a bare metal instance, and Nova enables
the node's console for them:

.. code-block:: console

 $ openstack console url show --novnc $SERVER

If the Nova image is older than 2026.1, this request fails with a "not
supported" error.

Nova waits up to 60 seconds for a node's console to start. To change that, set
the timeout in seconds:

.. code-block:: yaml

    nova_helm_values:
      conf:
        nova_ironic:
          ironic:
            vnc_console_state_timeout: 120
