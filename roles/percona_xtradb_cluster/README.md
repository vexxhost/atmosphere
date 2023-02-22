# percona_xtradb_cluster

## Scheduled backups

For more details on how to configure backups, you can refer to the
[scheduled backups documentation](https://docs.percona.com/percona-operator-for-mysql/pxc/backups.html#making-scheduled-backups)
for the Percona Operator for MySQL.

You can override the default backup settings by setting the
`percona_xtradb_cluster_spec` variable inside your inventory.  You can use the
following examples as a starting point.

## Local storage

The following example shows a backup that runs daily at 6AM to a persistent
volume with 3 backups kept.  The size of the persistent volume is 50Gi in the
example below.

> **Note**
>
> The Percona Operator for MySQL creates a persistent volume claim for every
> single backup.  This means that if you have 3 backups kept, you will have 3
> persistent volume claims.  It's best to set the storage in that case to the
> size of a single backup (or perhaps match your backup size to the size of the
> cluster storage, which defaults to `160Gi`).

```yaml
percona_xtradb_cluster_spec:
  backup:
    image: percona/percona-xtradb-cluster-operator:1.10.0-pxc5.7-backup
    storages:
      fs-pvc:
        type: filesystem
        volume:
          persistentVolumeClaim:
            accessModes:
              - ReadWriteOnce
            resources:
              requests:
                storage: 50Gi
    schedule:
      - name: daily
        schedule: 0 6 * * *
        keep: 3
        storageName: fs-pvc
```
