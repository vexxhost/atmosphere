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

In order to evacuate a compute node, you will need to start by disabling the
OpenStack compute service on the node.  This will prevent new workloads from
being scheduled on the node.  To disable the OpenStack compute service, run
the following command against the node you want to evacuate:

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
