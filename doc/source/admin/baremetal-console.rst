#############################
Bare metal graphical consoles
#############################

Atmosphere can give bare metal nodes the same browser-based graphical console
that virtual machines have. When a console is opened, the Ironic conductor
starts a short-lived Pod that signs in to the node's BMC web console and serves
it over VNC. ``ironic-novncproxy`` and ``nova-novncproxy`` carry that session
to the browser.

Graphical consoles are disabled by default.

.. note::

    For more details about how Ironic implements graphical consoles, refer to
    the `Ironic graphical console documentation
    <https://docs.openstack.org/ironic/latest/install/graphical-console.html>`_.

Requirements
============

- Ironic and Nova images from the OpenStack 2026.1 release or later. Ironic
  added the Kubernetes console provider in 2026.1, and Nova added VNC consoles
  for bare metal instances in the same release.
- A console container image for your BMC vendor. Atmosphere does not ship one.
  Upstream Ironic provides one in ``tools/vnc-container`` that supports Dell
  iDRAC, HPE iLO and Supermicro BMCs. Any image you use must implement Ironic's
  ``APP``, ``APP_INFO`` and ``READ_ONLY`` environment variables and accept VNC
  connections on TCP port 5900.
- A DNS record for the console hostname. It defaults to the Ironic API
  hostname with its first label replaced by ``baremetal-console``, so an API at
  ``baremetal.cloud.example.com`` gets a console at
  ``baremetal-console.cloud.example.com``. Set
  ``openstack_helm_endpoints_ironic_novnc_host`` to use a different name, which
  must not be the same as the Ironic API hostname.

Enable graphical consoles
=========================

Turn the feature on and point it at your console image. The image must be
pinned by digest, and the deployment stops if it isn't:

.. code-block:: yaml

    ironic_vnc_enabled: true
    atmosphere_image_overrides:
      ironic_console: registry.example.com/ironic-console@sha256:<digest>

With this configuration, Atmosphere:

- deploys ``ironic-novncproxy`` behind its own Ingress on the console hostname,
- configures the Ironic conductor to start console Pods in the
  ``openstack-ironic-vnc`` namespace, which you can change with
  ``ironic_vnc_namespace``,
- enables the ``redfish-graphical`` and ``no-console`` console interfaces,
- applies a NetworkPolicy that lets only ``ironic-novncproxy`` and
  ``nova-novncproxy`` reach the console Pods.

Leave the NetworkPolicy on unless you manage network policies for that
namespace yourself, in which case set
``ironic_vnc_network_policy_enabled: false``.

The noVNC browser files for both proxies come from the Nova image. To use
different ones, override ``ironic_novncproxy_assets`` or
``nova_novncproxy_assets`` in ``atmosphere_image_overrides`` with a
digest-pinned image that contains ``/usr/share/novnc``.

Open a console on a node
========================

Select the graphical console interface on each node whose BMC your console
image supports, then enable the console and get its URL:

.. code-block:: console

 $ openstack baremetal node set $NODE --console-interface redfish-graphical
 $ openstack baremetal node console enable $NODE
 $ openstack baremetal node console show $NODE

In the example above, ``$NODE`` is the name or UUID of the bare metal node.

.. note::

    Do not make ``redfish-graphical`` the default console interface if your
    deployment has hardware that the console image doesn't support. Set it on
    each supported node instead.

Open a console on a bare metal instance
=======================================

Users reach consoles for their bare metal instances through Nova, the same way
they do for virtual machines. Nova needs ``nova-compute-ironic``, which is not
deployed by default. Enable it with:

.. code-block:: yaml

    nova_helm_values:
      manifests:
        statefulset_compute_ironic: true

Users can then get a console URL for a bare metal instance:

.. code-block:: console

 $ openstack console url show --novnc $SERVER

If the Nova image is older than 2026.1, this request fails with a "not
supported" error.

Nova needs no other changes. Atmosphere already allows both the ``vencrypt``
and ``none`` VNC authentication schemes, so the proxy can reach the console
Pod, which offers no authentication, while hypervisors keep using VeNCrypt.
Nova waits up to 60 seconds for a node's console to start. To change that, set
the timeout in seconds:

.. code-block:: yaml

    nova_helm_values:
      conf:
        nova_ironic:
          ironic:
            vnc_console_state_timeout: 120

Disable graphical consoles
==========================

Disable the console on every node first, so that no console Pods are left
running:

.. code-block:: console

 $ openstack baremetal node console disable $NODE

Then turn the feature off:

.. code-block:: yaml

    ironic_vnc_enabled: false

If any console Pods or their credential Secrets still exist, the deployment
stops before it changes the console setup, so that open sessions aren't cut
off.
