Preparing hosts for eVMCS
=========================

Hyper-V enlightened VMCS (eVMCS) is an Intel-specific optimization for nested
Hyper-V workloads. See :doc:`/user/windows/evmcs` for benefits and image
configuration.

Host prerequisites
------------------

Upgrade all Nova services to an image with eVMCS support before offering the
feature. Use Intel KVM compute hosts with nested virtualization enabled and VMX
exposed to guests by the configured guest CPU model.

Nova requires the ``HW_CPU_X86_INTEL_VMX`` Placement trait for images that
request eVMCS. Check an intended compute host:

.. code-block:: console

   $ COMPUTE_UUID=$(openstack resource provider list --name <compute-host> -f value -c uuid)
   $ openstack resource provider trait list "$COMPUTE_UUID"

Confirm that ``HW_CPU_X86_INTEL_VMX`` is present. This trait is a scheduling
prerequisite; it doesn't replace checking nested virtualization and the guest
CPU model. AMD hosts aren't eligible for eVMCS. Don't manually add the Intel
trait to an unsupported host.

Rollout
-------

Validate a Windows canary with VBS or Hyper-V enabled, including performance
and migration between the intended hosts, before wider use. QEMU notes that
eVMCS disables some virtualization features, including posted interrupts, so
benchmark the workload with and without it. See the `QEMU Hyper-V documentation
<https://www.qemu.org/docs/master/system/i386/hyperv.html#existing-enlightenments>`_.

Users enable eVMCS through :doc:`image properties </user/windows/evmcs>`; don't
add ``hv-evmcs`` to ``cpu_model_extra_flags``. eVMCS is a Hyper-V enlightenment,
and this change doesn't add Mode-Based Execution Control (MBEC) support.
