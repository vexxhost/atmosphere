# `cinder`

## Operations

### Auditing orphan attachments

It's possible that over time, there are some volumes that have attachments which
are no longer valid.  This can happen when a server is being deleted via Nova
but the request to delete the volume and the attachment fails.  You can get
a list of volumes which have attachments that are no longer valid by running
the following command:

```bash
for volume in $(openstack volume list --all-projects --status in-use -c ID -f value | tac); do
  for server in $(openstack volume show $volume -f json| jq -r '.attachments[0].server_id'); do
    name=$(openstack server show $server -c name -f value 2>&1)

    if [ "$name" = "No server with a name or ID of '$server' exists." ]; then
      echo openstack volume set --detached $volume
      echo openstack volume delete $volume
    else
      echo "Volume $volume is attached to $name"
    fi
  done
done
```

> **Note**
>
> You can optionally replace `--all-projects` by `--project <project_id>` in the
> `openstack volume list` command to filter the volumes by project.

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
