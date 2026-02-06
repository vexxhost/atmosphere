#################
Maintenance Guide
#################

This guide provides instructions for regular maintenance tasks necessary to
ensure the smooth and secure operation of the system.

********************************
Evacuating Nodes for Maintenance
********************************

When you need to perform maintenance on a node, you will need to evacuate the
node to ensure that no workloads are running on it.   Depending on the type of
node you are evacuating, you will need to use different commands.

Control Plane Node
==================

To evacuate a control plane node, you will need to drain the node.  This will
cause all the control plane components to be moved to other nodes in the
cluster.  To drain a control plane node, run the following command against
the node you want to drain:

.. code-block:: console

    $ kubectl drain <node-name> --ignore-daemonsets --delete-local-data <node-name>

In the example above, you would replace ``<node-name>`` with the name of the
node you want to drain.  Once this process is complete, you can safely perform
maintenance on the node.

When you are done with the maintenance, you can uncordon the node by running
the following command:

.. code-block:: console

    $ kubectl uncordon <node-name>

Compute Node
============

Before initiating VM evacuation, it is important to understand the implications for
different types of instances:

---------------------------
Boot from Volume Instances:
---------------------------

These instances have their root disks stored on a distributed storage system (e.g., Ceph).
Evacuating these instances is safe and ensures that data integrity is maintained
since the root volume is detached from the failing hypervisor and reattached to a
new one.

-------------------------------
Non-Boot from Volume Instances:
-------------------------------

These instances have their root disks stored locally on the hypervisor's ephemeral
storage. Evacuating these instances will result in the loss of all data stored
in the root disk.

.. admonition:: warning
    Evacuation of non-boot-from-volume instances should be avoided unless data loss
    is acceptable or has been mitigated through backups or other mechanisms.

The evacuation process can be divided into two scenarios based on the state of
the hypervisor: when the hypervisor is up or down. 

The hypervisor is still up:
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to evacuate a compute node with the hypervisor running, you will need to 
start by disabling the OpenStack compute service on the node. This will prevent 
new workloads from being scheduled on the node.  

To disable the OpenStack compute service, run the following command against
the node you want to evacuate:

.. code-block:: console

    $ openstack compute service set --disable <node-name> nova-compute

In the example above, you would replace ``<node-name>`` with the name of the
node you want to evacuate.  Once the OpenStack compute service has been
disabled, you will need to evacuate all the virtual machines running on the
node.  To do this, run the following command:

.. code-block:: console

    $ nova host-evacuate-live <node-name>

In the example above, you would replace ``<node-name>`` with the name of the
node you want to evacuate.  This command will live migrate all the virtual
machines running on the node to other nodes in the cluster.

.. admonition:: Note

    It is generally not recommended to use the ``nova`` client however the
    ``nova host-evacuate-live`` command is not available in the ``openstack``
    client (see `bug 2055552 <https://bugs.launchpad.net/python-openstackclient/+bug/2055552>`_).

You can monitor the progress of this operation by seeing if there are any VMs
left on the node by running the following command:

.. code-block:: console

    $ openstack server list --host <node-name>

Once all the virtual machines have been evacuated, you can safely perform
maintenance on the node.  When you are done with the maintenance, you can
reenable the OpenStack compute service by running the following command:

.. code-block:: console

    $ openstack compute service set --enable <node-name> nova-compute

.. admonition:: Note

    Once you enable the compute service, the node will start accepting new
    VMs but it will not automatically move the VMs back to the node.  You will
    need to manually move the VMs back to the node if you want them to run
    there.

The hypervisor is down and unreachable:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a hypervisor becomes unreachable, live evacuation will not function 
as communication with the source host is no longer possible. As highlighted 
above, attempting to evacuate virtual machines (VMs) that are not booted from 
a volume will result in data loss. This happens because the system/root disk 
will be recreated from the original image stored in Glance, rather than preserving 
any changes made after deployment.

This scenario commonly arises when a compute node becomes inoperable and needs 
replacement. In such cases, migrating ephemeral workloads becomes necessary. 
Users must understand that if there are no backups in place, all data in /root will likely be lost.

We generally recommend using ephemeral storage only for workloads where critical or 
long-lived data is not a requirement and performance is the primary concern. 
A typical example of ephemeral resource usage is virtual machines deployed for CI/CD systems.

*********************
Renewing Certificates
*********************

The certificates used by the Kubernetes cluster are valid for one year.  They
are automatically renewed when the cluster is upgraded to a new version of
Kubernetes.  However, if you are running the same version of Kubernetes for
more than a year, you will need to manually renew the certificates.

To renew the certificates, run the following command on each one of your
control plane nodes:

.. code-block:: console

    $ sudo kubeadm certs renew all

Once the certificates have been renewed, you will need to restart the
Kubernetes control plane components to pick up the new certificates.  You need
to do this on each one of your control plane nodes by running the following
command one at a time on each node:

.. code-block:: console

    $ ps auxf | egrep '(kube-(apiserver|controller-manager|scheduler)|etcd)' | awk '{ print $2 }' | xargs sudo kill

*************************************
Changing controller network addresses
*************************************

Changing the IP address of an existing controller node is a complex operation
that affects multiple critical components of the Atmosphere deployment.
The recommended approach is to remove and redeploy the controller node
rather than attempting an in-place IP change.

Components affected by address changes
======================================

When a controller node's IP address changes, the following components are
directly impacted:

* **etcd cluster**: The etcd cluster stores its member list with specific IP
  addresses. Changing an IP requires careful reconfiguration of the cluster
  membership.

* **Ceph monitors**: If Ceph monitors are running on controller nodes, they
  maintain a monitor map with specific IP addresses that must remain consistent
  across the cluster.

* **Kubernetes API server**: The API server advertises its address to other
  components, and certificates may tie to specific IP addresses.

* **Virtual IP**: The virtual IP configuration depends on the underlying
  node IP addresses for proper fail-over behavior.

* **DNS resolution**: The fully qualified domain names (FQDNs) in the inventory
  must resolve to the correct IP addresses.

* **Network policies and firewall rules**: Any security policies that reference
  specific controller IP addresses require updates.

Recommended procedure
=====================

To change a controller node's IP address, follow this procedure:

1. **Plan the maintenance window**: This operation will temporarily reduce the
   control plane's redundancy. Make sure you have adequate time and that the
   remaining controllers can handle the load.

2. **Verify cluster health**: Before proceeding, confirm all components are
   healthy:

   .. code-block:: console

       $ kubectl get nodes
       $ kubectl get pods -n openstack
       $ kubectl get pods -n kube-system
       $ ceph status  # if Ceph is deployed

3. **Drain the controller node**: Follow the standard procedure to evacuate
   the controller node:

   .. code-block:: console

       $ kubectl drain <node-name> --ignore-daemonsets --delete-local-data

4. **Remove the node from the cluster**:

   .. code-block:: console

       $ kubectl delete node <node-name>

5. **Remove etcd member** (if the node runs etcd):

   First, identify the etcd member ID:

   .. code-block:: console

       $ kubectl -n kube-system exec etcd-<remaining-controller> -- etcdctl \
         --endpoints=https://127.0.0.1:2379 \
         --cacert=/etc/kubernetes/pki/etcd/ca.crt \
         --cert=/etc/kubernetes/pki/etcd/server.crt \
         --key=/etc/kubernetes/pki/etcd/server.key \
         member list

   Then remove the member:

   .. code-block:: console

       $ kubectl -n kube-system exec etcd-<remaining-controller> -- etcdctl \
         --endpoints=https://127.0.0.1:2379 \
         --cacert=/etc/kubernetes/pki/etcd/ca.crt \
         --cert=/etc/kubernetes/pki/etcd/server.crt \
         --key=/etc/kubernetes/pki/etcd/server.key \
         member remove <member-id>

6. **Update inventory**: Modify your inventory to reflect the new IP
   address for the controller node. Verify the FQDN resolves to the new IP.

7. **Update DNS records**: Update any DNS records to point the controller's
   FQDN to the new IP address. Verify resolution:

   .. code-block:: console

       $ nslookup <controller-fqdn>

8. **Clean up the old node**: On the node itself, clean up Kubernetes and etcd
   data:

   .. code-block:: console

       $ sudo kubeadm reset -f
       $ sudo rm -rf /etc/cni/net.d
       $ sudo rm -rf /var/lib/etcd

9. **Redeploy the controller**: Run the Atmosphere playbooks to rejoin the node
   to the cluster with its new IP address. The exact playbook depends on your
   deployment method.

10. **Verify the new configuration**: After the node rejoins, verify:

    .. code-block:: console

        $ kubectl get nodes
        $ kubectl get pods -n kube-system | grep etcd
        $ kubectl cluster-info

Alternative approach for multiple controllers
=============================================

If you need to change IP addresses for multiple controllers, consider deploying
new controllers with the correct IP addresses first, then removing the old ones.
This approach maintains higher availability throughout the process:

1. Deploy new controller nodes with the desired IP addresses
2. Wait for them to fully join the cluster and synchronize
3. Remove the old controller nodes one at a time

.. warning::

   Never attempt to change IP addresses on all controllers simultaneously.
   This will result in a complete control plane outage and potential data loss.

.. admonition:: Important Considerations

   * Always maintain quorum in the etcd cluster (majority of nodes operational)
   * Test this procedure in a non-production environment first
   * Have backups of critical data before proceeding
   * Consider the impact on any external systems that may reference controller IP addresses
   * Some components may cache old IP addresses and require restart
