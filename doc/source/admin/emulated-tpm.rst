#######################################
Emulated Trusted Platform Module (vTPM)
#######################################

Atmosphere ships with the vTPM features enabled by default, so you just need
to verify that it's setup optionally and either configure a flavor or an image
to use it.

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
or through image metadata properties which can be set by the user. There are two
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

Image configuration
-------------------

You can also configure the vTPM on an image using the ``hw_tpm_version`` and
``hw_tpm_model`` image metadata properties. For example, to configure an image
to use the TPM 2.0 with CRB model:

.. code-block:: console

 $ openstack image set <image-name-or-uuid> \
     --property hw_tpm_version=2.0 \
     --property hw_tpm_model=tpm-crb

This can be useful if you need to enable the vTPM feature without having operator
access to the cloud or for specific images such as Windows versions that require
a TPM to be present.

Create an instance with vTPM
============================

Once you've configured the vTPM, you can create an instance using the flavor or
image you configured. For example, to create an instance using the flavor we
created previously:

.. code-block:: console

 $ openstack server create --flavor test.vtpm test-instance

Or using an image:

.. code-block:: console

 $ openstack server create --image <image-name-or-uuid> test-instance

The instance should now have the vTPM device available.
