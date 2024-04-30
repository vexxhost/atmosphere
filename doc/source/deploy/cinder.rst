####################
Cinder Configuration
####################

Cinder, the block storage service for OpenStack, can be configured to use a
variety of storage backends. This section guides you through setting up Cinder
with different backend technologies, each of which might require specific
configuration steps.

********
Ceph RBD
********

When using the integrated Ceph cluster provided with Atmosphere, no additional
configuration is needed for Cinder. The deployment process automatically
configures Cinder to use Ceph as the backend, simplifying setup and integration.

***************
Dell PowerStore
***************

In order to be able to use Dell PowerStore, you'll need to make sure that you
setup the hosts inside of your storage array. You'll also need to make sure
that they are not inside a host group or otherwise individual attachments will
not work.

You can enable the native PowerStore driver for Cinder with the following
configuration inside your Ansible inventory:

.. code-block:: yaml

    cinder_helm_values:
      storage: powerstore
      dependencies:
        static:
          api:
            jobs:
              - cinder-db-sync
              - cinder-ks-user
              - cinder-ks-endpoints
              - cinder-rabbit-init
          scheduler:
            jobs:
              - cinder-db-sync
              - cinder-ks-user
              - cinder-ks-endpoints
              - cinder-rabbit-init
          volume:
            jobs:
              - cinder-db-sync
              - cinder-ks-user
              - cinder-ks-endpoints
              - cinder-rabbit-init
          volume_usage_audit:
            jobs:
              - cinder-db-sync
              - cinder-ks-user
              - cinder-ks-endpoints
              - cinder-rabbit-init
      conf:
        cinder:
          DEFAULT:
            enabled_backends: powerstore
            default_volume_type: powerstore
        backends:
          rbd1: null
          powerstore:
            volume_backend_name: powerstore
            volume_driver: cinder.volume.drivers.dell_emc.powerstore.driver.PowerStoreDriver
            san_ip: <FILL IN>
            san_login: <FILL IN>
            san_password: <FILL IN>
            storage_protocol: <FILL IN> # FC or iSCSI
      manifests:
        deployment_backup: true
        job_backup_storage_init: true
        job_storage_init: false

    nova_helm_values:
      conf:
        enable_iscsi: true

.. admonition:: About ``conf.enable_iscsi``
    :class: info

    The ``enable_iscsi`` setting is required to allow the Nova instances to
    expose volumes by making the `/dev` devices available to the containers,
    not necessarily to use iSCSI as the storage protocol. In this case, the
    PowerStore driver will use the storage protocol specified inside Cinder,

********
StorPool
********

Using StorPool as a storage backend requires additional configuration to ensure
proper integration. These adjustments include network settings and file system mounts.

Configure Cinder to use StorPool by implementing the following settings:

.. code-block:: yaml

    cinder_helm_values:
      storage: storpool
      pod:
        useHostNetwork:
          volume: true
        mounts:
          cinder_volume:
            volumeMounts:
              - name: etc-storpool-conf
                mountPath: /etc/storpool.conf
                readOnly: true
              - name: etc-storpool-conf-d
                mountPath: /etc/storpool.conf.d
                readOnly: true
            volumes:
              - name: etc-storpool-conf
                hostPath:
                  type: File
                  path: /etc/storpool.conf
              - name: etc-storpool-conf-d
                hostPath:
                  type: Directory
                  path: /etc/storpool.conf.d
      dependencies:
        static:
          api:
            jobs:
              - cinder-db-sync
              - cinder-ks-user
              - cinder-ks-endpoints
              - cinder-rabbit-init
          scheduler:
            jobs:
              - cinder-db-sync
              - cinder-ks-user
              - cinder-ks-endpoints
              - cinder-rabbit-init
          volume:
            jobs:
              - cinder-db-sync
              - cinder-ks-user
              - cinder-ks-endpoints
              - cinder-rabbit-init
          volume_usage_audit:
            jobs:
              - cinder-db-sync
              - cinder-ks-user
              - cinder-ks-endpoints
              - cinder-rabbit-init
      conf:
        cinder:
          DEFAULT:
            enabled_backends: hybrid-2ssd
            default_volume_type: hybrid-2ssd
        backends:
          rbd1: null
          hybrid-2ssd:
            volume_backend_name: hybrid-2ssd
            volume_driver: cinder.volume.drivers.storpool.StorPoolDriver
            storpool_template: hybrid-2ssd
            report_discard_supported: true
      manifests:
        deployment_backup: false
        job_backup_storage_init: false
        job_storage_init: false

    nova_helm_values:
      conf:
        enable_iscsi: true

.. admonition:: About ``conf.enable_iscsi``
    :class: info

    The ``enable_iscsi`` setting is required to allow the Nova instances to
    expose volumes by making the `/dev` devices available to the containers,
    not necessarily to use iSCSI as the storage protocol. In this case, the
    StorPool devices will be exposed as block devices to the containers.
