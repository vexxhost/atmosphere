#####################
Database backup guide
#####################

This guide provides instructions how to backup and restore database.

*****************
Scheduled backups
*****************

For more details on how to configure backups, you can refer to the
`scheduled backups documentation <https://docs.percona.com/percona-operator-for-mysql/pxc/backups-scheduled.html>`_
for the Percona Operator for MySQL.

You can override the default backup settings by setting the
``percona_xtradb_cluster_spec`` variable inside your inventory. You can use the
following examples as a starting point.

Persistent volume
=================

The following example shows a backup that runs daily at 6 AM to a persistent
volume with 3 backups kept. The size of the persistent volume is 50Gi in the
example below:

.. admonition:: Note
  :class: note

  The Percona Operator for MySQL creates a persistent volume claim for every
  single backup. This means that if you have 3 backups kept, you will have 3
  persistent volume claims. It's best to set the storage to the size of a
  single backup (or perhaps match your backup size to the size of the
  cluster storage, which defaults to ``160Gi``).

.. code-block:: yaml

  percona_xtradb_cluster_spec:
    backup:
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
          retention:
            type: "count"
            count: 3
            deleteFromStorage: true
          storageName: fs-pvc

Amazon S3 or s3-compatible storage
==================================

To store backups on the Amazon S3, you need to create a Secret with the following values:

.. code-block:: yaml

  apiVersion: v1
  kind: Secret
  metadata:
    name: pxc-backup-s3
  type: Opaque
  data:
    AWS_ACCESS_KEY_ID: # base64-encoded value of access key
    AWS_SECRET_ACCESS_KEY: # base64-encoded value of secret access key

.. code-block:: shell

  kubectl -n openstack apply -f /path/to/secret.yaml

The following example shows a backup that runs daily at 6 AM to an Amazon S3 or
S3-compatible storage with 3 backups kept.

.. code-block:: yaml

  percona_xtradb_cluster_spec:
    backup:
      storages:
        s3-bck:
          type: s3
          s3:
            # You can specify the path (sub-folder) to the backups inside the S3 bucket:
            # bucket: atmosphere-pxc-backup-1234/region-x
            # If prefix is not set, backups are stored in the root directory.
            bucket: atmosphere-pxc-backup-1234
            region: us-east-1
            # If you use some S3-compatible storage instead of the original Amazon S3:
            # endpointUrl: https://s3.rgw.ceph.endpoint
            # or
            # endpointUrl: https://storage.googleapis.com
            credentialsSecret: pxc-backup-s3
      schedule:
        - name: daily
          schedule: 0 6 * * *
          retention:
            type: "count"
            count: 3
            deleteFromStorage: true
         storageName: s3-bck

*****************
On-demand backups
*****************

To make an on-demand backup, you should first check your Custom Resource
for the necessary options and make changes, if needed. The ``backup.storages``
subsection should contain at least one configured storage.

Examples:

.. code-block:: yaml

  apiVersion: pxc.percona.com/v1
  kind: PerconaXtraDBClusterBackup
  metadata:
    finalizers:
      # Finalizer can be set even if you use a persistent volume.
      - percona.com/delete-backup
    name: backup1-pvc
  spec:
    pxcCluster: percona-xtradb
    storageName: fs-pvc

.. code-block:: yaml

  apiVersion: pxc.percona.com/v1
  kind: PerconaXtraDBClusterBackup
  metadata:
    finalizers:
      - percona.com/delete-backup
    name: backup1-s3
  spec:
    pxcCluster: percona-xtradb
    storageName: s3-bck

.. code-block:: shell

  kubectl -n openstack apply -f /path/to/backup.yaml

Track the backup process by checking the status of the Backup object:

.. code-block:: shell

  kubectl -n openstack get pxc-backup -w

*********************************
Restore the cluster from a backup
*********************************

Find the correct backup names. Use the following command to list the available backups:

.. code-block:: shell

  kubectl -n openstack get pxc-backup

Examples:

Restore with a name from a backup CRD list:

.. code-block:: yaml

  apiVersion: pxc.percona.com/v1
  kind: PerconaXtraDBClusterRestore
  metadata:
    name: restore1-from-pvc
  spec:
    pxcCluster: percona-xtradb
    backupName: backup1-pvc

Restore from a remote location without a backup name when the system deletes
the backup CRD or when another cluster creates the backup:

.. code-block:: yaml

  apiVersion: pxc.percona.com/v1
  kind: PerconaXtraDBClusterRestore
  metadata:
    name: restore1-from-remote-s3
  spec:
    pxcCluster: percona-xtradb
    backupSource:
      destination: s3://atmosphere-pxc-backup-1234/region-x/backup1-s3
      s3:
        credentialsSecret: pxc-backup-s3
        region: us-east-1

.. code-block:: shell

  kubectl -n openstack apply -f /path/to/restore.yaml

***********************************
Backup performance related settings
***********************************

This example is for relatively large clusters with a lot of data.

.. admonition:: Warning
  :class: warning

  Keep in mind that configuration settings aren't merged with the default
  settings. If you set any value in the configuration you also have to set all parameters from
  ``_percona_xtradb_cluster_spec.pxc.configuration`` defaults.

.. code-block:: yaml

  percona_xtradb_cluster_spec:
    pxc:
      configuration: |
        [mysqld]
        max_connections=8192
        innodb_buffer_pool_size=8G
        # Skip reverse DNS lookup of clients
        skip-name-resolve
        pxc_strict_mode=MASTER
        innodb_buffer_pool_instances=4
        innodb_thread_concurrency=4
        innodb_flush_sync=OFF
        wsrep_applier_threads=4
        wsrep_restart_replica=ON
        [sst]
        # We are using huge value for sst idle timeout because
        # script which is responsible for backup restoration size
        # detection is not aware about time needed for transferred
        # data decompression
        # BUG: https://perconadev.atlassian.net/browse/PXC-3951
        sst-idle-timeout=36000
        xbstream-opts="--decompress --decompress-threads=4 --parallel=4"
        inno-apply-opts="--use-memory=6G"
        inno-backup-opts="--parallel=4"
        [xtrabackup]
        # https://docs.percona.com/percona-xtrabackup/8.0/xtrabackup-option-reference.html#compress
        compress
        compress-threads=4
        read-buffer-size=100M
        parallel=4
        use-memory=6G
        rebuild-threads=4
        [xbcloud]
        parallel=4
