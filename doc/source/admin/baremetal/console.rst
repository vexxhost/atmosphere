##################
Graphical consoles
##################

Bare metal nodes get the same browser-based graphical console as virtual
machines. It is enabled by default whenever Ironic is deployed and works with
Dell iDRAC, HPE iLO and Supermicro BMCs through Redfish.

Graphical consoles need Ironic and Nova from the OpenStack 2026.1 release or
later.

Open a console on a bare metal instance
=======================================

Users open consoles for their bare metal instances through Nova, the same way
they do for virtual machines:

.. code-block:: console

 $ openstack console url show --novnc $SERVER

Open a console on a node
========================

New nodes that use the ``redfish`` hardware type get the
``redfish-graphical`` console interface automatically. Nodes enrolled earlier
keep their existing interface, so switch them once:

.. code-block:: console

 $ openstack baremetal node set $NODE --console-interface redfish-graphical

Administrators can also open a node's console directly through Ironic:

.. code-block:: console

 $ openstack baremetal node console enable $NODE
 $ openstack baremetal node console show $NODE

The URL points at ``ironic-novncproxy``, which is only reachable inside the
cluster. Forward it to your machine and replace the host and port in the URL
with ``localhost:6090``:

.. code-block:: console

 $ kubectl -n openstack port-forward svc/ironic-novncproxy 6090

Disable the console when you are done:

.. code-block:: console

 $ openstack baremetal node console disable $NODE

Security
========

Each open console runs in its own Pod in the ``openstack-ironic-vnc``
namespace, which enforces the restricted Pod Security Standard. The Pods run
on control plane nodes as a non-root user without a service account token.
Only the Ironic and Nova console proxies can connect to them, and they can
only make outbound DNS and HTTP(S) connections, so the BMC web interface must
be reachable on port 80 or 443.

Restrict web traffic to BMC networks
----------------------------------

The default egress rules allow HTTP(S) to any destination. To prevent console
Pods from reaching unrelated web services, override ``console.egress`` with
the BMC management subnets. For example, replace ``192.0.2.0/24`` below with
your BMC network:

.. code-block:: yaml

    ironic_helm_values:
      console:
        egress:
          - to:
              - namespaceSelector:
                  matchLabels:
                    kubernetes.io/metadata.name: kube-system
                podSelector:
                  matchLabels:
                    k8s-app: kube-dns
            ports:
              - protocol: UDP
                port: 53
              - protocol: TCP
                port: 53
          - to:
              - ipBlock:
                  cidr: 192.0.2.0/24
            ports:
              - protocol: TCP
                port: 80
              - protocol: TCP
                port: 443

This list replaces the default rules, so retain DNS access when the BMC
addresses use hostnames. For a BMC emulator running in Kubernetes, select
its namespace and Pods instead of using an IP block, and allow the port
used by those Pods.
