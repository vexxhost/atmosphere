#################
CSI Configuration
#################

This section details how to configure Container Storage Interfaces (CSI) for
your Kubernetes cluster that Atmosphere runs on. You will need to follow the
steps below to enable specific CSI drivers based on your storage requirements.

.. admonition:: Storing secrets securely
    :class: tip

    When configuring CSI drivers, it is important to store sensitive
    information securely. You can use Ansible Vault to encrypt your inventory
    file and store it in a secure location. For more information on how to
    use Ansible Vault, refer to the `Ansible documentation <https://docs.ansible.com/ansible/latest/user_guide/vault.html>`_.

********
Ceph RBD
********

If you are using the Ceph storage solution that Atmosphere deploys out of the
box, no additional configuration is required. The necessary settings are
automatically applied during the installation process.

***************
Dell PowerStore
***************

For environments requiring the integration of PowerStore for storage,
configure the PowerStore CSI driver by updating your Ansible inventory as
follows:

.. code-block:: yaml

    csi_driver: powerstore
    powerstore_csi_config:
      arrays:
        - endpoint: https://<FILL IN>/api/rest
          globalID: <FILL IN>
          username: <FILL IN>
          password: <FILL IN>
          skipCertificateValidation: true
          isDefault: true
          blockProtocol: <FILL IN> # FC or iSCSI

Ensure that you replace ``<FILL IN>`` with actual values relevant to your
PowerStore configuration. This includes specifying the block protocol, which
can either be Fibre Channel (FC) or iSCSI, depending on your network
infrastructure.

*********
IBM Block
*********

If you're using a storage array that is compatible with the IBM Block CSI
driver, you can configure it by updating your Ansible inventory as follows:

.. code-block:: yaml

    csi_driver: ibm_block
    ibm_block_csi_driver_management_address: <FILL IN>
    ibm_block_csi_driver_username: <FILL IN>
    ibm_block_csi_driver_password: <FILL IN>
    ibm_block_csi_driver_pool: <FILL IN>
    ibm_block_csi_driver_io_group: <FILL IN>

Optionally, you can control the ``SpaceEfficiency`` setting which defaults to
`thin` to enable thin provisioning.  To change it to any other value, you
can set the following variable:

.. code-block:: yaml

    ibm_block_csi_driver_space_efficiency: <FILL IN>

Ensure that you replace ``<FILL IN>`` with actual values relevant to your IBM
Block configuration.  You can use the `Creating a StorageClass <https://www.ibm.com/docs/en/stg-block-csi-driver/1.11.3?topic=configuring-creating-storageclass>`_
documentation to help you determine the values to use.

********
Portworx
********

If you are using a Pure Storage array for your block storage, you can use the
Portworx CSI driver to integrate it with your Kubernetes cluster.  Portworx
automatically enables a custom license when integrated with Pure Storage
arrays (FA/FB edition).

To configure the Portworx CSI driver, update your Ansible inventory as follows:

.. code-block:: yaml

    csi_driver: portworx
    portworx_pure_flasharray_san_type: <FILL IN> # FC or ISCSI
    portworx_pure_json:
      FlaskBlades: []
      FlashArrays:
        - MgmtEndPoint: <FILL IN>
          APIToken: <FILL IN>

For more information about how the ``portworx_pure_json`` variable is used,
you can refer to the `Pure Storage FlashArray and FlashBlade JSON file reference <https://docs.portworx.com/portworx-enterprise/reference/pure-reference/pure-json-reference>`_.

********
StorPool
********

For environments requiring the integration of StorPool for storage, configure
the StorPool CSI driver by updating your Ansible inventory as follows:

.. code-block:: yaml

    csi_driver: storpool
    storpool_csi_template: k8s

The ``storpool_csi_template`` variable specifies the StorPool template to use
for the deployment which is set to ``k8s`` in the example above.
