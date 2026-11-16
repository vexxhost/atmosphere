Windows guests
==============

Use these guides to configure Windows images and instances. Cloud operators
should also read :doc:`/admin/windows/index` for host prerequisites.

Security and performance
------------------------

Windows security features have different requirements:

* :doc:`../emulated-tpm` explains how to provide TPM 2.0 for Windows 11 and
  features such as TPM-backed BitLocker key protection. vTPM support isn't
  restricted to Intel hosts.
* :doc:`evmcs` describes an Intel-specific optimization for guests running
  Hyper-V, including virtualization-based security (VBS) and memory integrity
  (HVCI). It can reduce nested virtualization overhead while those features
  remain enabled.

vTPM and eVMCS serve different purposes and can be configured independently.
Neither setting enables VBS inside Windows.

.. toctree::
   :maxdepth: 2

   evmcs
