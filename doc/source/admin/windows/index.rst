Windows guest administration
============================

Prepare the cloud to support the features described in the
:doc:`/user/windows/index` user guide.

* Follow :doc:`evmcs` to prepare Intel compute hosts and roll out Nova support
  for nested Hyper-V workloads.
* Use :doc:`/admin/emulated-tpm` to verify vTPM support and offer TPM-enabled
  flavors. vTPM isn't restricted to Windows or Intel hosts.

Users configure their images using the linked user guides. Administrators who
maintain shared Windows images can use the same instructions.

.. toctree::
   :maxdepth: 2

   evmcs
