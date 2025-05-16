###############################
Secure Encrypted Virtualization
###############################

Atmosphere comes with SEV support pre-configured and automatically enabled
for all compatible hardware. To use this feature, you simply need to:

- Verify SEV is available on your host

- Configure either your flavor or image to use memory encryption

You don't need to perform any additional host-level configuration to enable
this security feature.

Enabling SEV for Workloads
==========================

Verify host’s capability
------------------------

You can verify that SEV support on your compute host, please executer:

.. code-block:: console

 $ virsh domcapabilities | grep sev

You should look for the line:

.. code-block:: xml

 <sev supported='yes'/>


Recommended configuration
-------------------------

- Ensure that sufficient memory is reserved on the SEV compute hosts for
  host-level services to function correctly at all times.
  
  It's recommended to achieve this by configuring an ``rlimit`` at the
  ``/machine.slice`` top-level ``cgroup`` on the host, with all Virtual Machines
  placed inside that.

  An alternative approach is to configure the
  ``reserved_host_memory_mb`` option in the
  ``[DEFAULT]`` section of ``nova.conf``, based on the expected maximum number of
  SEV guests simultaneously running on the host.

- Configure ``ram_allocation_ratio`` on all SEV-capable compute hosts
  to ``1.0``. Use of SEV requires locking guest memory, meaning it's not possible
  to overcommit host memory.

- Configure ``libvirt.hw_machine_type`` on all SEV-capable compute
  hosts to include ``x86_64=q35``, so that all x86_64 images use the ``q35`` machine
  type by default.

Note: We've eliminated the legacy ``num_memory_encrypted_guests`` setting as Atmosphere 
uses libvirt 8.0.0 which handles SEV capacity dynamically.

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

 $ openstack server create --flavor test.sev test-instance

Or using an image:

.. code-block:: console

 $ openstack server create --image <image-name-or-uuid> test-instance

The instance should now have the SEV available.