##########
Ceph Guide
##########

*****************************************
Placement groups (``PGs``) and autoscaling
*****************************************

In Ceph, placement groups (``PGs``) are an important abstraction that help
distribute objects across the cluster. Each ``PG`` can be thought of as a logical
collection of objects and Ceph uses these ``PGs`` to assign data to the appropriate
``OSDs`` (Object Storage Daemons). The proper management of ``PGs`` is critical to
ensure the health and performance of your Ceph cluster.

The number of ``PGs`` must be carefully configured depending on the size and layout
of your cluster. The cluster performance can be negatively impacted if you
have too many or too few placement groups.

To learn more about placement groups and their role in Ceph, refer to the
`placement groups <https://docs.ceph.com/en/latest/rados/operations/placement-groups/>`_
documentation from the Ceph project.

The primary recommendations for a Ceph cluster is the following:

- Enable placement group autoscaling
- Enable the Ceph balancer module to ensure data is evenly distributed across ``OSDs``

The following sections provide guidance on how to enable these features in your
Ceph cluster.

Enabling ``PG`` autoscaling
===========================

Ceph provides a built-in placement group autoscaling module, which can
dynamically adjust the number of ``PGs`` based on cluster utilization. This is
particularly useful as it reduces the need for manual intervention when
scaling your cluster up or down.

To enable ``PG`` autoscaling, execute the following command in your Ceph cluster:

.. code-block:: console

   $ ceph mgr module enable pg_autoscaler

You can configure autoscaling to be on a per-pool basis by setting the target
size or percentage of the cluster you want a pool to occupy. For example,
to enable autoscaling for a specific pool:

.. code-block:: console

   $ ceph osd pool set <pool_name> pg_autoscale_mode on

For more detailed instructions, refer to the `Autoscaling Placement Groups <https://docs.ceph.com/en/reef/rados/operations/placement-groups/#autoscaling-placement-groups>`_
documentation from the Ceph project.

Managing the Ceph Balancer
==========================

The Ceph Balancer tool helps redistribute data across ``OSDs`` in order to maintain
an even distribution of data in the cluster. This is especially important as
the cluster grows, new ``OSDs`` are added, or during recovery operations.

To enable the balancer, run:

.. code-block:: console

   $ ceph balancer on

You can check the current balancer status using:

.. code-block:: console

   $ ceph balancer status

For a more in-depth look at how the balancer works and how to configure it,
refer to the `Balancer module <https://docs.ceph.com/en/latest/rados/operations/balancer/>`_
documentation from the Ceph project.
