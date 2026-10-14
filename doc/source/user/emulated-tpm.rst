Using a virtual TPM
===================

A virtual Trusted Platform Module (vTPM) provides a TPM device to an instance.
Use TPM 2.0 for Windows 11 or features such as TPM-backed BitLocker key
protection. Other guest operating systems can also use vTPM; it isn't
restricted to Intel hosts.

Before you begin
----------------

Ask your cloud operator to confirm :doc:`/admin/emulated-tpm` support and
whether a TPM-enabled flavor is available. If you configure image properties,
use an image you own or have permission to modify. Its TPM settings must be
compatible with the selected flavor.

Configure an image
------------------

Set TPM 2.0 with the CRB model before creating instances:

.. code-block:: console

   $ openstack image set <image-name-or-uuid> \
       --property hw_tpm_version=2.0 \
       --property hw_tpm_model=tpm-crb

Create an instance using that image and a compatible flavor:

.. code-block:: console

   $ openstack server create <instance-name> \
       --image <image-name-or-uuid> \
       --flavor <flavor-name-or-uuid> \
       --network <network-name-or-uuid>

If your operator provides a TPM-enabled flavor, you can use it without setting
TPM image properties. Changing image properties doesn't update existing
instances.

Related Windows features
------------------------

See :doc:`windows/index` for Windows security and performance guidance. vTPM
provides a TPM device; :doc:`eVMCS <windows/evmcs>` reduces nested Hyper-V
overhead on Intel hosts. They can be configured independently, and neither
setting enables VBS or BitLocker inside the guest.
