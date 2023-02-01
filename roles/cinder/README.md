# `cinder`

## Configuring backup storage

Cinder supports a wide variety of storage backends to store volume backups. They
can be referenced from the [Cinder documentation](https://docs.openstack.org/cinder/latest/configuration/block-storage/backup-drivers.html).

### Ceph

It is possible to backup volumes into a Ceph cluster.  You are able to store
the backups inside the same Ceph cluster that is deployed by Atmosphere or an
external cluster that you deploy.

#### Atmosphere

If you're looking to use the Ceph cluster that is deployed by Atmosphere, you
will need to simply set the following inventory variables:

```yaml
cinder_helm_values:
  conf:
    cinder:
      DEFAULT:
        backup_driver: cinder.backup.drivers.ceph.CephBackupDriver
```

> **Warning**
>
> It's not recommended to use same backend for volumes and backups. If you are
> using Atmosphere's Ceph for volumes, you should use a different Ceph cluster
> for backups.

#### External

If you want to use an external Ceph cluster, you will need to set the following
inventory variables:

```yaml
cinder_helm_values:
  conf:
    cinder:
      DEFAULT:
        backup_driver: cinder.backup.drivers.ceph.CephBackupDriver
        backup_ceph_user: cinder
        backup_ceph_pool: backups
  backup:
    external_ceph_rbd:
      enabled: true
      admin_keyring: AQCBYNhjMtiXEBAA3weDsYA2zoPqOXTRijQtzg==
      conf:
        global:
          fsid: 795115d3-2b3d-567f-b5f8-72703d896b56
          mon host: 10.96.240.153,10.96.240.126,10.96.240.240
```

Atmosphere will automatically create a `cephx` user which matches the provided
`backup_ceph_user` variable.  It will also create a pool with the name of the
`backup_ceph_pool` variable.
