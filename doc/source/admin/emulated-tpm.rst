#######################################
Emulated Trusted Platform Module (vTPM)
#######################################


Starting in the 22.0.0 (Victoria) release, Nova supports adding an emulated virtual
Trusted Platform Module (vTPM) to guests.

The vTPM feature is enabled by default, so just verify and configure the flavor with
vTPM.

Verify the configuration
========================

Verify vTPM support by inspecting the traits on the compute node’s resource provider:

.. code-block:: console
   
 $ COMPUTE_UUID=$(openstack resource provider list --name $HOST -f value -c uuid)
 $ openstack resource provider trait list $COMPUTE_UUID | grep SECURITY_TPM
 | COMPUTE_SECURITY_TPM_1_2 |
 | COMPUTE_SECURITY_TPM_2_0 |


Configuring a flavor or image
=============================

A vTPM can be requested on a server via flavor extra specs or image metadata properties.
There are two versions supported - 1.2 and 2.0 - and two models - TPM Interface
Specification (TIS) and Command-Response Buffer (CRB). The CRB model is only supported 
with version 2.0.

For example, to configure a flavor to use the TPM 2.0 with the CRB model:

.. code-block:: console

   $ openstack flavor create test.vtpm \
    --ram 512 --disk 1 --vcpus 1  \
    --property hw:tpm_version=2.0 \
    --property hw:tpm_model=tpm-crb


Create an instance with vTPM
============================
With configuration complete, we can finally proceed to creating an instance. Simply create
an instance using the flavor we created previously.
