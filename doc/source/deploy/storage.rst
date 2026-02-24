#####################
Storage Configuration
#####################

Atmosphere uses a unified storage configuration variable ``atmosphere_storage``
that serves as the single source of truth for all storage backends across
OpenStack services. This eliminates the need to configure storage settings in
multiple places.

********
Overview
********

The ``atmosphere_storage`` variable is organized by storage purpose:

``images``
  Image storage for Glance. Supports multiple backends.

``volumes``
  Block storage for Cinder. Supports multiple backends.

``backups``
  Backup storage for Cinder backup.

``ephemeral``
  Ephemeral disk storage for Nova and libvirt.

The system automatically derives per-service Helm values from this single
variable for Cinder, Glance, Nova, libvirt, and Ceph Provisioners.

***************
Default Configuration
***************

By default, Atmosphere configures all services to use the integrated Ceph
cluster:

.. code-block:: yaml

    atmosphere_storage:
      images:
        default: rbd1
        backends:
          rbd1:
            type: ceph_rbd
            pool: glance.images
            replication: 3
            crush_rule: replicated_rule
            chunk_size: 8
            ceph_user: glance
      volumes:
        default: rbd1
        backends:
          rbd1:
            type: ceph_rbd
            pool: cinder.volumes
            replication: 3
            crush_rule: replicated_rule
            ceph_user: cinder
            secret_uuid: 457eb676-33da-42ec-9a8c-9293d545c337
      backups:
        type: ceph_rbd
        pool: cinder.backups
        replication: 3
        crush_rule: replicated_rule
        ceph_user: cinderbackup
      ephemeral:
        type: ceph_rbd
        pool: vms
        replication: 3
        crush_rule: replicated_rule
        ceph_user: cinder
        secret_uuid: 457eb676-33da-42ec-9a8c-9293d545c337

No additional configuration is needed when using the integrated Ceph cluster.

*************
Backend Types
*************

Ceph RBD (``ceph_rbd``)
========================

Standard replicated Ceph RBD backend. Used for images, volumes, backups, and
ephemeral storage.

.. code-block:: yaml

    type: ceph_rbd
    pool: <pool_name>
    replication: 3
    crush_rule: replicated_rule
    ceph_user: <username>
    secret_uuid: <uuid>       # required for volumes and ephemeral

Ceph RBD Erasure-Coded (``ceph_rbd_ec``)
=========================================

Erasure-coded Ceph RBD backend for improved storage efficiency. Only supported
for volume backends.

.. code-block:: yaml

    type: ceph_rbd_ec
    pool: cinder.volumes.ec
    erasure_coded:
      k: 4                     # data chunks
      m: 2                     # coding (parity) chunks
      failure_domain: host
      device_class: hdd        # optional
    metadata_replication: 3
    ceph_user: cinder-ec       # must be unique per EC backend
    secret_uuid: <unique-uuid>

.. warning::

    Each erasure-coded backend requires a **dedicated** ``ceph_user`` and a
    **unique** ``secret_uuid``. Generate new UUIDs with ``uuidgen``.

Dell PowerStore (``powerstore``)
================================

.. code-block:: yaml

    type: powerstore
    san_ip: <management_ip>
    san_login: <username>
    san_password: <password>
    storage_protocol: iSCSI    # or FC

Pure Storage (``pure``)
=======================

.. code-block:: yaml

    type: pure
    volume_driver: cinder.volume.drivers.pure.PureISCSIDriver
    san_ip: <management_ip>
    pure_api_token: <token>

StorPool (``storpool``)
=======================

.. code-block:: yaml

    type: storpool
    storpool_template: hybrid-2ssd

Cinder (``cinder``)
====================

Cinder-backed Glance store. Only used for image backends.

.. code-block:: yaml

    type: cinder

********
Examples
********

Adding an erasure-coded volume backend
======================================

To add an EC pool alongside the default replicated backend, add a new entry
under ``atmosphere_storage.volumes.backends``:

.. code-block:: yaml

    atmosphere_storage:
      volumes:
        backends:
          rbd_ec:
            type: ceph_rbd_ec
            pool: cinder.volumes.ec
            erasure_coded:
              k: 4
              m: 2
              failure_domain: host
            metadata_replication: 3
            ceph_user: cinder-ec
            secret_uuid: 808c5658-7c46-4818-8f26-82a217e3a57a

The system automatically configures all required services: Cinder backend
configuration, Ceph pool creation, libvirt secret registration, and Ceph
client data pool routing.

Using Dell PowerStore
=====================

.. code-block:: yaml

    atmosphere_storage:
      volumes:
        default: powerstore
        backends:
          powerstore:
            type: powerstore
            san_ip: 10.0.0.1
            san_login: admin
            san_password: secret
            storage_protocol: iSCSI
      backups:
        type: none
      ephemeral:
        type: local

Glance with multiple backends
=============================

.. code-block:: yaml

    atmosphere_storage:
      images:
        default: rbd1
        backends:
          rbd1:
            type: ceph_rbd
            pool: glance.images
            replication: 3
            ceph_user: glance
          cinder_store:
            type: cinder

*******************
Advanced Overrides
*******************

The ``atmosphere_storage`` variable generates base Helm values. You can still
use per-service ``*_helm_values`` variables (such as ``cinder_helm_values`` or
``glance_helm_values``) to override specific settings. The per-service overrides
always take precedence.
