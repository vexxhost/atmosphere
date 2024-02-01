# Cinder (Block Storage Service)

## Built-in Ceph cluster

## External storage

When using an external storage platform, it's important to create to disable Ceph
globally by adding the following to your Ansible inventory:

```yaml
atmosphere_ceph_enabled: false
```

### Dell PowerStore

In order to be able to use Dell PowerStore, you'll need to make sure that you
setup the hosts inside of your storage array. You'll also need to make sure
that they are not inside a host group or otherwise individual attachments will
not work.

#### CSI

You'll need to enable the Kubernetes cluster to use the PowerStore driver by
using adding the following YAML to your Ansible inventory:

```yaml
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
```

#### Glance

Since Glance does not have a native PowerStore driver, you'll need to enable
the use of the Cinder driver by adding the following to your Ansible inventory:

```yaml
glance_helm_values:
  storage: cinder
  conf:
    glance:
      glance_store:
        stores: cinder
        default_store: cinder
      image_formats:
        disk_formats: raw
```

Please note that Glance images will not function until the Cinder service is
deployed. In addition, we're forcing all images to be `raw` format in order to
avoid any issues with the PowerStore driver having to constantly download and
upload the images.

#### Cinder

You can enable the native PowerStore driver for Cinder with the following
configuration inside your Ansible inventory:

```yaml
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
```

It's important to note that the configuration above will disable the Cinder
backup service. In the future, we'll update this sample configuration to use
the Cinder backup service.

#### Nova

You can enable the native PowerStore driver for Cinder with the following
configuration inside your Ansible inventory:

```yaml
nova_helm_values:
  conf:
    enable_iscsi: true
```

!!! note

    The PowerStore driver will use the storage protocol specified inside Cinder,
    even if the above mentions `iscsi`.
