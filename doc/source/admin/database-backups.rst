#################
Database Backup Guide
#################

This guide provides instructions how to backup database.

********************************
Scheduled backups
********************************

For more details on how to configure backups, you can refer to the
`scheduled backups documentation <https://docs.percona.com/percona-operator-for-mysql/pxc/backups-scheduled.html>`_
for the Percona Operator for MySQL.

You can override the default backup settings by setting the
``percona_xtradb_cluster_spec`` variable inside your inventory. You can use the
following examples as a starting point.

Persistent Volume
==================

The following example shows a backup that runs daily at 6 AM to a persistent
volume with 3 backups kept. The size of the persistent volume is 50Gi in the
example below:

.. admonition:: Note
  :class: note

  The Percona Operator for MySQL creates a persistent volume claim for every
  single backup. This means that if you have 3 backups kept, you will have 3
  persistent volume claims. It's best to set the storage in that case to the
  size of a single backup (or perhaps match your backup size to the size of the
  cluster storage, which defaults to ``160Gi``).

.. code-block:: yaml

  percona_xtradb_cluster_spec:
    backup:
      image: percona/percona-xtradb-cluster-operator:1.14.0-pxc8.0-backup-pxb8.0.35
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

Amazon S3 or S3-Compatible Storage
===================================

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
      image: percona/percona-xtradb-cluster-operator:1.14.0-pxc8.0-backup-pxb8.0.35
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
          keep: 3
         storageName: s3-bck
