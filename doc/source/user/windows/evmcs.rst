Hyper-V enlightened VMCS
========================

Windows guests that run Hyper-V, including for virtualization-based security
(VBS) and memory integrity (HVCI), can use enlightened VMCS (eVMCS) to reduce
nested virtualization overhead. This can improve performance when these
features are active; the benefit depends on the workload. Benchmark with and
without eVMCS: QEMU notes that it disables some virtualization features,
including posted interrupts, which can offset the benefit.

Before you begin
----------------

Your cloud must support eVMCS and have eligible Intel compute hosts. Ask your
cloud operator to confirm the :doc:`/admin/windows/evmcs` prerequisites. eVMCS
is Intel-only; this restriction doesn't apply to Windows or vTPM generally.

Use a Windows image you own or have permission to modify. Configure Hyper-V or
VBS inside Windows as needed; the image property doesn't enable them. For TPM
requirements, see :doc:`/user/emulated-tpm`.

Enable eVMCS
------------

Set these properties on the Windows image before creating instances:

.. code-block:: console

   $ openstack image set <image-name-or-uuid> \
       --property os_type=windows \
       --property hw_hyperv_evmcs=true

Create new instances from that image. Updating image properties doesn't change
existing instances. If no eligible Intel host is available, scheduling fails
with ``No valid host``; ask your cloud operator to check host eligibility
and capacity.

eVMCS is disabled by default. To disable it for future instances, set
``hw_hyperv_evmcs=false`` on the image. This feature doesn't add Mode-Based
Execution Control (MBEC) support.
