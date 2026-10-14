#######################################
Emulated Trusted Platform Module (vTPM)
#######################################

Atmosphere enables vTPM support by default. This guide covers host capability
checks and administrator-managed flavors. Users can follow
:doc:`/user/emulated-tpm` to configure their own images and create instances.

Verify the configuration (optional)
===================================

You can verify that the vTPM support is activated by inspecting the traits on
the compute nodes resource provider:

.. code-block:: console

 $ COMPUTE_UUID=$(openstack resource provider list --name $HOST -f value -c uuid)
 $ openstack resource provider trait list $COMPUTE_UUID | grep SECURITY_TPM
 | COMPUTE_SECURITY_TPM_1_2 |
 | COMPUTE_SECURITY_TPM_2_0 |

In the example above, ``$HOST`` is the hostname of the compute node where you
want to verify that vTPM support is enabled.

Configuring vTPM
================

The vTPM can be configured using flavor extra specs (which requires an operator)
or through image metadata properties which can be set by the user.  There are two
versions supported:

- 1.2
- 2.0

In addition, there are two models supported:

- TPM Interface Specification (TIS)
- Command-Response Buffer (CRB)

.. note::

    The CRB model is only supported with version 2.0 which is the recommended
    option as well.

Flavor configuration
--------------------

You can use the ``hw:tpm_version`` and ``hw:tpm_model`` properties to configure
the vTPM on a flavor. For example, to configure a flavor to use the TPM 2.0 with
the CRB model:

.. code-block:: console

 $ openstack flavor create test.vtpm \
     --ram 512 --disk 1 --vcpus 1  \
     --property hw:tpm_version=2.0 \
     --property hw:tpm_model=tpm-crb

User configuration
------------------

For image properties and instance creation, see :doc:`/user/emulated-tpm`.
Administrators maintaining shared images can use the same instructions.
For related host preparation, see :doc:`windows/index`.
