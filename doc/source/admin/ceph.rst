##########
Ceph Guide
##########

***************************************
Placement Groups (PGs) and Auto-scaling
***************************************

In Ceph, Placement Groups (PGs) are an important abstraction that help
distribute objects across the cluster. Each PG can be thought of as a logical
collection of objects and Ceph uses these PGs to assign data to the appropriate
OSDs (Object Storage Daemons).  The proper management of PGs is critical to
ensure the health and performance of your Ceph cluster.

The number of PGs must be carefully configured depending on the size and layout
of your cluster.   The cluster performance can be negatively impacted if you
have too many or too few placement groups.

To learn more about placement groups and their role in Ceph, refer to the
`placement groups <https://docs.ceph.com/en/latest/rados/operations/placement-groups/>`_
documentation from the Ceph project.

The primary recommendations for a Ceph cluster is the following:

- Enable placement group auto-scaling
- Enable the Ceph balancer module to ensure data is evenly distributed across OSDs

The following sections provide guidance on how to enable these features in your
Ceph cluster.

Enabling PG Auto-scaling
========================

Ceph provides a built-in placement group auto-scaling module, which can
dynamically adjust the number of PGs based on cluster utilization. This is
particularly useful as it reduces the need for manual intervention when
scaling your cluster up or down.

To enable PG auto-scaling, execute the following command in your Ceph cluster:

.. code-block:: console

   $ ceph mgr module enable pg_autoscaler

You can configure auto-scaling to be on a per-pool basis by setting the target
size or percentage of the cluster you want a pool to occupy.  For example,
to enable auto-scaling for a specific pool:

.. code-block:: console

   $ ceph osd pool set <pool_name> pg_autoscale_mode on

For more detailed instructions, refer to the `Autoscaling Placement Groups <https://docs.ceph.com/en/reef/rados/operations/placement-groups/#autoscaling-placement-groups>`_
documentation from the Ceph project.

Managing the Ceph Balancer
==========================

The Ceph Balancer tool helps redistribute data across OSDs in order to maintain
an even distribution of data in the cluster.  This is especially important as
the cluster grows, new OSDs are added, or during recovery operations.

To enable the balancer, run:

.. code-block:: console

   $ ceph balancer on

You can check the current balancer status using:

.. code-block:: console

   $ ceph balancer status

For a more in-depth look at how the balancer works and how to configure it,
refer to the `Balancer module <https://docs.ceph.com/en/latest/rados/operations/balancer/>`_
documentation from the Ceph project.

Rebuilding OSD with WAL/DB
==========================

Rebuilding OSDs wtih WAL/DB one by one with SSD partitioning gives you much finer control over data movement and reduces cluster stress. Here's the step-by-step process:

Phase 1: Prepare SSD Partitioning Strategy
------------------------------------------

Step 1: Select Target SSD for DB Device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Choose the least utilized SSD per node. For example:

- **ceph1**: OSD.20 (69.19% utilization - best candidate)
- **ceph2**: Similar pattern
- Continue for other nodes

Step 2: Create SSD Partitions Before Migration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, you need to prepare partitions on the target SSD while it's still an active OSD:

.. code-block:: console

    # SSH to target node
    $ ssh ceph1

    # Identify the SSD device path for OSD.20
    $ ceph-volume lvm list | grep osd.20
    # Example output shows: /dev/sdd

    # Calculate partition sizes for 18 HDDs
    # For example 1.7TB SSD / 18 HDDs = ~94GB tper partition
    # Leave some space for overhead, use 90GB per partition

Phase 2: Controlled OSD-by-OSD Migration
----------------------------------------

Step 3: Remove Target SSD OSD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # Remove the SSD OSD that will become DB device
    $ ceph orch osd rm ceph1:osd.20 --replace

    # Monitor data migration
    $ ceph -w
    $ ceph osd df | grep -E "9[0-9]%"  # Watch for near-full OSDs

Wait for complete data migration before proceeding.

Step 4: Partition the Freed SSD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    # On ceph1, partition the SSD
    $ ssh ceph1
    
    # Clear the device first
    $ lvremove <block device>
    $ pvremove <devices>
    $ ceph-volume lvm zap /dev/sdd --destroy
    
    # Create 18 partitions for DB offload
    $ parted /dev/sdd mklabel gpt
    
    # Create partitions (90GB each)
    for i in {1..18}; do
      start=$((($i-1)*90))GB
      end=$(($i*90))GB
      parted /dev/sdd mkpart primary ${start} ${end}
    done
    
    # Verify partitions
    $ lsblk /dev/sdd
    
Step 5: Migrate HDDs One by One
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now migrate each HDD OSD individually:

.. code-block:: console

    # Start with the first HDD OSD (e.g., OSD.2)
    $ echo "Migrating OSD.2..."
    
    # Remove the HDD OSD
    $ ceph orch osd rm ceph1:osd.2 --replace
    
    # Monitor migration progress
    while ceph pg stat | grep -qE "(remapped|degraded)"; do
      echo "Waiting for data migration to complete..."
      ceph pg stat
      sleep 30
    done
    
    # Recreate OSD.2 with SSD DB offload using first partition
    $ ceph-volume lvm create \
      --data /dev/sdX \
      --block.db /dev/sdd1
    
    $ echo "OSD.2 migration complete"

Step 6: Validate Each Migrated OSD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # Check that HDDs now have SSD DB offload
    for osd in $(ceph osd ls-tree ceph1 | grep hdd); do
        echo "OSD $osd:"
        ceph osd metadata $osd | grep -E "bluefs|devices|osd_objectstore"
    done

Advantages of This Approach
------------------------------

Granular Control:
^^^^^^^^^^^^^^^^^
- Move only 1 OSD worth of data at a time (~3TB max)
- Cluster remains fully functional throughout
- Can pause/resume migration at any point

Risk Mitigation:
^^^^^^^^^^^^^^^^
- Failure affects only 1 OSD, not entire node
- Easy rollback if issues arise
- Continuous monitoring of cluster health

Resource Management:
^^^^^^^^^^^^^^^^^^^^
- Lower network bandwidth usage
- Controlled rebalancing load
- Predictable migration timeline (~30 minutes per OSD)

Performance Optimization:
^^^^^^^^^^^^^^^^^^^^^^^^^^
- Each HDD gets dedicated DB partition (90GB)
- No shared SSD contention during heavy writes
- Immediate performance improvement per migrated OSD
