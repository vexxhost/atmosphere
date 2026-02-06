###############################################
Virtual Persistent Memory (vPMEM)
###############################################

Atmosphere includes support for virtual persistent memory (vPMEM), which allows
instances to use persistent memory devices. This feature requires the ``ndctl``
package to be installed on compute nodes, which is already included in the
default images.

Virtual persistent memory provides non-volatile memory that persists across
instance reboots and can offer performance benefits for certain workloads that
require low-latency access to persistent storage.

.. note::

    For more information about virtual persistent memory in OpenStack Nova,
    refer to the `OpenStack Nova documentation
    <https://docs.openstack.org/nova/latest/admin/virtual-persistent-memory.html>`_.

Prerequisites
=============

The compute nodes must have the ``ndctl`` package installed. This package is
included by default in Atmosphere Nova images, so no additional configuration
is required on the compute hosts.

Verify the configuration (optional)
====================================

You can verify that vPMEM support is activated by checking the resource
providers and traits on the compute nodes:

.. code-block:: console

 $ COMPUTE_UUID=$(openstack resource provider list --name $HOST -f value -c uuid)
 $ openstack resource provider trait list $COMPUTE_UUID | grep COMPUTE_PMEM

In the example above, ``$HOST`` is the hostname of the compute node where you
want to verify that vPMEM support is enabled.

Configuring vPMEM
=================

Virtual persistent memory can be configured using flavor extra specs (which
requires operator access) or through image metadata properties (which can be
set by users). The configuration defines the size and label of the vPMEM device
that will be attached to instances.

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
property. This allows users to request vPMEM without requiring operator access.

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
Inside the guest operating system, the device will appear as ``/dev/pmem0`` (or
``/dev/pmem1``, etc., for multiple devices).

Using vPMEM in the guest
=========================

Once the instance is created with vPMEM, the guest operating system needs to
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

.. note::

    The guest operating system must also have ``ndctl`` installed to manage
    the vPMEM devices. This is separate from the ``ndctl`` package required
    on the compute hosts.
