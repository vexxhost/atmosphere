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

In the example above, ``$HOST`` is the ``hostname`` of the compute node where you
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

Automatic VM restart after compute node reboot
==============================================

When a compute node reboots, Nova attempts to restart vTPM-enabled virtual
machines automatically. However, this requires Nova to access Barbican secrets
that store the vTPM data. By default, Nova can't access secrets created in user
projects, which causes the virtual machine restart to fail.

Atmosphere provides configuration options to allow Nova to access these secrets.

.. warning::

   Enabling these options has security implications. When enabled, the Nova
   service account or users with the admin role can access any secret in
   Barbican, not just vTPM-related secrets. Consider the security implications
   before enabling these options.

Enabling Nova service access
----------------------------

To allow the Nova service account to access Barbican secrets for vTPM operations,
add the following to your inventory:

.. code-block:: yaml

   barbican_policy_nova_secret_access: true

This allows the Nova service user (which has the ``service`` role) to read and
decrypt any secret in Barbican. This is the recommended option if you need
automatic vTPM VM restart after compute node reboots.

Enabling admin access
---------------------

To allow users with the admin role to access all Barbican secrets, add the
following to your inventory:

.. code-block:: yaml

   barbican_policy_admin_secret_access: true

This is useful for administrative tasks and troubleshooting, but it reduces
secret isolation between projects.

Combining both options
----------------------

Both options can be enabled together:

.. code-block:: yaml

   barbican_policy_admin_secret_access: true
   barbican_policy_nova_secret_access: true

Security considerations
-----------------------

When these options are enabled:

- **Nova service access**: The Nova service account can read any secret in
  Barbican, including secrets that aren't related to vTPM. This is necessary
  because Nova needs to decrypt vTPM data stored in user projects.

- **Admin access**: Users with the admin role in any project can read secrets
  from other projects. This breaks the default project-level isolation of
  Barbican secrets.

If you use Barbican for storing sensitive data beyond vTPM (such as encryption
keys for volumes or other applications), consider the impact of enabling these
options on your security posture.
