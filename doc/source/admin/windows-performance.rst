Windows performance
===================

Hyper-V enlightened VMCS
------------------------

Windows guests that run Hyper-V, including for virtualization-based security
(VBS) and memory integrity (HVCI), can use enlightened VMCS (eVMCS) to reduce
nested virtualization overhead. This can improve performance when these
features are active; the benefit depends on the workload.

Requirements
~~~~~~~~~~~~

Use Intel KVM compute hosts with nested virtualization enabled and VMX exposed
to the guest. Nova schedules images that request eVMCS only on hosts advertising
the ``HW_CPU_X86_INTEL_VMX`` Placement trait. AMD hosts aren't eligible.

Upgrade all Nova services to an image with eVMCS support before enabling it.
eVMCS doesn't enable Hyper-V or VBS inside Windows; configure those features in
the guest as needed. For Windows images that need a
TPM, see :doc:`emulated-tpm`.

Enable eVMCS
~~~~~~~~~~~~

Set these properties on the Windows image before creating instances:

.. code-block:: console

   $ openstack image set <image-name-or-uuid> \
       --property os_type=windows \
       --property hw_hyperv_evmcs=true

Create new instances from that image. Updating image properties doesn't change
existing instances. If no eligible Intel host is available, scheduling fails
with ``No valid host``.

eVMCS is disabled by default. To disable it for future instances, set
``hw_hyperv_evmcs=false`` on the image. This feature doesn't add Mode-Based
Execution Control (MBEC) support.
