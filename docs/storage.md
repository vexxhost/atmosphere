# Storage

## Enable RBD persistent write-back cache

There are frequently cases of environments that sustain write-heavy loads which can overwhelm the underlying storage OSDs. It's also possible that non-enterprise 3D NAND flash is in use with small memory buffers which can do fast upfront writes but unable to sustain those writes.

In those environments, it's possible that a lot of slow operations will start to cumulate inside of the cluster, which will bubble up as performance issues inside the virtual machines.  This can be highly impactful on workloads, increase the latency of the VMs and drop IOPs down to near zero.

There are environments that have local storage on all of the RBD clients (in this case, VMs) which can potentially be backed by battery backed hardware RAID with a local cache.  This can significantly drive down the latency and increase write speeds since they are persisted onto the local system.  The only fallback is that if the client crashes (or hypervisor in this case), the data won't easily be recoverable, however, this is a small risk to take in workloads replacing the storage infrastructure is not realistic and the stability of systems is relatively high.

### Configuring compute hosts

There are a few steps that needs to be done on the underlying operating system
which runs the compute nodes. The steps bellow assumes that a device `/deb/<dev>`
is already setup accordingly to the host's storage capabilities.

1. Create filesystem for cache:

    ```yaml
    mkfs.ext4 /dev/<dev>
   ```

2. Get fs uuid
   ```yaml
    blkid
   ```

3. Add record to mount filesystem in `/etc/fstab`:
   ```yaml
   UUID="XXXXX"	/var/lib/libvirt/rbd-cache ext4	defaults	0	1
   ```

4. Create folder for cache
   ```yaml
    mkdir /var/lib/libvirt/rbd-cache
   ```

5. Mount the cache
    ```yaml
    mount /var/lib/libvirt/rbd-cache
    ```

### Enabling rbd write-back cache

In order to be able to confirgure write-back cache, you need to override the following
values for ceph provisioners to your Ansible inventory:

```yaml
openstack_helm_infra_ceph_provisioners_values:
  conf:
    ceph:
      global:
        rbd_plugins: pwl_cache
        rbd_persistent_cache_mode: ssd
        rbd_persistent_cache_path: /var/lib/libvirt/rbd-cache
        rbd_persistent_cache_size: 30G
```

### Verifying

Once the configurations are applied to the ceph provisioners, once you create a virtual machine backed by ceph, you should be able to see a file for cache inside `/var/lib/libvirt/rbd-cache`:

```yaml
/var/lib/libvirt# ls -l rbd-cache/
total 344
drwxrwxr-x 2 42424 syslog       16384 Nov 30 20:38 lost+found
-rw-r--r-- 1 42424 syslog 29999759360 Dec  1 17:37 rbd-pwl.cinder.volumes.a8eba89efc83.pool
```

 > **Note**
>
> For existing vms to take advantage of write-back cache, you will need
to hard reboot them.


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

### CSI

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

### Glance

Since Glance does not have a native PowerStore driver, you'll need to enable
the use of the Cinder driver by adding the following to your Ansible inventory:

```yaml
openstack_helm_glance_values:
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

### Cinder

You can enable the native PowerStore driver for Cinder with the following
configuration inside your Ansible inventory:

```yaml
openstack_helm_cinder_values:
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

### Nova

You can enable the native PowerStore driver for Cinder with the following
configuration inside your Ansible inventory:

```yaml
openstack_helm_nova_values:
  conf:
    enable_iscsi: true
```

> **Note**
>
> The PowerStore driver will use the storage protocol specified inside Cinder,
> even if the above mentions `iscsi`.
