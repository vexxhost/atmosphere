#################
CSI Configuration
#################

This section details how to configure Container Storage Interfaces (CSI) for
your Kubernetes cluster that Atmosphere runs on. You will need to follow the
steps below to enable specific CSI drivers based on your storage requirements.

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
StorPool
********

For environments requiring the integration of StorPool for storage, configure
the StorPool CSI driver by updating your Ansible inventory as follows:

.. code-block:: yaml

    csi_driver: storpool
    storpool_csi_template: k8s

The ``storpool_csi_template`` variable specifies the StorPool template to use
for the deployment which is set to ``k8s`` in the example above.
