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
volume with 3 backups kept.  The size of the persistent volume is 500Gi in the
example below.

```yaml
percona_xtradb_cluster_spec:
  backup:
    image: perconalab/percona-xtradb-cluster-operator:main-pxc8.0-backup
    storages:
      fs-pvc:
        type: filesystem
        volume:
          persistentVolumeClaim:
            accessModes:
              - ReadWriteOnce
            resources:
              requests:
                storage: 500Gi
    schedule:
      - name: daily
        schedule: 0 6 * * *
        keep: 3
        storageName: fs-pvc
```
