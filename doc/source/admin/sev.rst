#########################################
AMD SEV (Secure Encrypted Virtualization)
#########################################

Atmosphere comes with SEV support pre-configured and automatically enabled
for all compatible hardware. To use this feature, you simply need to:

- Verify SEV is available on your host (optional but recommended)

- Configure either your flavor or image to utilize memory encryption

No additional host-level configuration is required to enable this security feature.

Enabling SEV
============

Verify host’s capability (optional)
-----------------------------------

You can verify that SEV support on your compute host, please executer:

.. code-block:: console

 $ virsh domcapabilities | grep sev

You should look for the line:

.. code-block:: xml

 <sev supported='yes'/>


Recommended configuration
-------------------------

- It is recommended to achieve this by configuring an ``rlimit`` at the
  ``/machine.slice`` top-level ``cgroup`` on the host, with all VMs placed inside that.

  An alternative approach is to configure the
  ``reserved_host_memory_mb`` option in the
  ``[DEFAULT]`` section of ``nova.conf`, based on the expected maximum number of
  SEV guests simultaneously running on the host.

- Configure the ``libvirt.num_memory_encrypted_guests`` option
  in ``nova.conf`` to represent the number of guests an SEV compute node can host
  concurrently with memory encrypted at the hardware level. For example:

  .. code-block:: ini

     [libvirt]
     num_memory_encrypted_guests = 15

- Configure ``ram_allocation_ratio`` on all SEV-capable compute hosts
  to ``1.0``. Use of SEV requires locking guest memory, meaning it is not possible to
  overcommit host memory.

- Configure ``libvirt.hw_machine_type`` on all SEV-capable compute
  hosts to include ``x86_64=q35``, so that all x86_64 images use the ``q35`` machine type
  by default.

Configuring SEV
================

The SEV can be configured using flavor extra specs (which requires an operator)
or through image metadata properties which can be set by the user.

Flavor configuration
--------------------

You can use the ``hw:mem_encryption`` properties to configure
the SEV on a flavor. For example:

.. code-block:: console

 $ openstack flavor create test.sev \
     --ram 512 --disk 1 --vcpus 1  \
     --property hw:mem_encryption=true

Image configuration
-------------------

You can also configure the SEV on an image using the ``hw_mem_encryption`` image
metadata properties. For example:

.. code-block:: console

 $ openstack image set <image-name-or-uuid> \
     --property hw_mem_encryption=true

This can be useful if you need to enable the SEV feature without having operator
access to the cloud or for specific images that require a SEV to be present.

Create an instance with SEV
===========================

Once you've configured the SEV, you can create an instance using the flavor or
image you configured. For example, to create an instance using the flavor we
created previously:

.. code-block:: console

 $ openstack server create --flavor test.vtpm test-instance

Or using an image:

.. code-block:: console

 $ openstack server create --image <image-name-or-uuid> test-instance

The instance should now have the SEV available.

Limitations
===========

Impermanent limitations
-----------------------

The following limitations may be removed in the future as the
hardware, firmware, and various layers of software receive new
features:

- SEV-encrypted VMs cannot yet be live-migrated or suspended,
  therefore they will need to be fully shut down before migrating off
  an SEV host, e.g. if maintenance is required on the host.

- SEV-encrypted VMs cannot contain directly accessible host devices
  (PCI passthrough).  So for example mdev vGPU support will not
  currently work.  However technologies based on `vhost-user`__ should
  work fine.

  __ https://wiki.qemu.org/Features/VirtioVhostUser

- The boot disk of SEV-encrypted VMs can only be ``virtio``.
  (``virtio-blk`` is typically the default for libvirt disks on x86,
  but can also be explicitly set e.g. via the image property
  ``hw_disk_bus=virtio``). Valid alternatives for the disk
  include using ``hw_disk_bus=scsi`` with
  ``hw_scsi_model=virtio-scsi`` , or ``hw_disk_bus=sata``.

Permanent limitations
---------------------

The following limitations are expected long-term:

- The number of SEV guests allowed to run concurrently will always be
  limited.  `On the first generation of EPYC machines it will be
  limited to 15 guests`__; however this limit becomes much higher with
  the second generation (Rome).

  __ https://www.redhat.com/archives/libvir-list/2019-January/msg00652.html

- The operating system running in an encrypted virtual machine must
  contain SEV support.

Non-limitations
---------------

For the sake of eliminating any doubt, the following actions are *not*
expected to be limited when SEV encryption is used:

- Cold migration or shelve, since they power off the VM before the
  operation at which point there is no encrypted memory (although this
  could change since there is work underway to add support for `PMEM
  <https://pmem.io/>`_)

- Snapshot, since it only snapshots the disk

- ``nova evacuate`` (despite the name, more akin to resurrection than
  evacuation), since this is only initiated when the VM is no longer
  running

- Attaching any volumes, as long as they do not require attaching via
  an IDE bus

- Use of spice / VNC / serial / RDP consoles

- ``VM guest virtual NUMA <cpu-topologies>``