###############################################
Virtual persistent memory (vPMEM)
###############################################

Atmosphere includes support for virtual persistent memory (vPMEM), which
provides instances with persistent memory devices. Virtual persistent memory
provides non-volatile memory that persists across instance reboots and can
offer performance benefits for certain workloads that require low-latency
access to persistent storage.

.. note::

    For more information about virtual persistent memory in OpenStack Nova,
    refer to the `OpenStack Nova documentation
    <https://docs.openstack.org/nova/latest/admin/virtual-persistent-memory.html>`_.

Verify the configuration (optional)
====================================

You can verify that vPMEM support is active by checking the resource
providers and traits on the compute nodes:

.. code-block:: console

 $ COMPUTE_UUID=$(openstack resource provider list --name $HOST -f value -c uuid)
 $ openstack resource provider trait list $COMPUTE_UUID | grep COMPUTE_PMEM

In the preceding example, ``$HOST`` is the host name of the compute node where
you want to verify that vPMEM support is active.

Configure vPMEM
===============

Virtual persistent memory configuration uses flavor extra specs (which
require operator access) or image metadata properties (which users can
set). The configuration defines the size and label of the vPMEM device
that will attach to instances.

Flavor configuration
--------------------

You can use the ``hw:pmem`` property to configure vPMEM on a flavor. The format
is ``$PMEM_LABEL=$SIZE``, where ``$PMEM_LABEL`` is an alphanumeric string
identifying the device and ``$SIZE`` is the size in GB.

For example, to configure a flavor with 4GB of vPMEM:

.. code-block:: console

 $ openstack flavor create test.pmem \
     --ram 2048 --disk 10 --vcpus 2 \
     --property hw:pmem=NVDIMM=4GB

You can also configure multiple vPMEM devices by separating them with commas:

.. code-block:: console

 $ openstack flavor create test.pmem.multi \
     --ram 2048 --disk 10 --vcpus 2 \
     --property hw:pmem=NVDIMM0=4GB,NVDIMM1=4GB

Image configuration
-------------------

You can also configure vPMEM on an image using the ``hw_pmem`` image metadata
property. This option lets users request vPMEM without requiring operator
access.

For example, to configure an image with 4GB of vPMEM:

.. code-block:: console

 $ openstack image set <image-name-or-uuid> \
     --property hw_pmem=NVDIMM=4GB

To configure multiple vPMEM devices:

.. code-block:: console

 $ openstack image set <image-name-or-uuid> \
     --property hw_pmem=NVDIMM0=4GB,NVDIMM1=4GB

Create an instance with vPMEM
==============================

Once you've configured vPMEM on a flavor or image, you can create an instance
that will have the vPMEM device attached.

Using a flavor:

.. code-block:: console

 $ openstack server create --flavor test.pmem --image <image-name-or-uuid> test-instance

Using an image:

.. code-block:: console

 $ openstack server create --flavor <flavor-name> --image <image-name-or-uuid> test-instance

The instance will have the vPMEM device available as a persistent memory device.
Inside the guest operating system, the device appears as ``/dev/pmem0`` (or
``/dev/pmem1`` for multiple devices).

Use vPMEM in the guest
=======================

Once you create the instance with vPMEM, the guest operating system needs to
configure and use the persistent memory device. The exact steps depend on the
guest operating system.

For Linux guests, you can use the ``ndctl`` utility to manage the persistent
memory devices:

.. code-block:: console

 # List available NVDIMM devices
 $ ndctl list

 # Create a namespace on the device
 $ ndctl create-namespace --mode=fsdax

 # Format and mount the device
 $ mkfs.ext4 /dev/pmem0
 $ mount /dev/pmem0 /mnt/pmem
