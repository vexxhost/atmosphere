# Creating a scheduled backup of a Percona Cluster

Use the following settings to setup a scheduled backup of every day at 6AM. This will write the backup to the persistent storage.

```yaml
percona_xtradb_cluster_spec:
  backup:
    image: perconalab/percona-xtradb-cluster-operator:main-pxc8.0-backup
    storages:
      fs-pvc:
        type: filesystem
        volume:
          persistentVolumeClaim:
            accessModes: [ "ReadWriteOnce" ]
            resources:
              requests:
                storage: 6Gi
    schedule:
      - name: "daily"
        schedule: "0 6 * * *"
        keep: 3
        storageName: fs-pvc
```
