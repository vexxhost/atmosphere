#####################
Storage configuration
#####################

Atmosphere uses a unified storage configuration variable ``atmosphere_storage``
that serves as the single source of truth for all storage backends across
OpenStack services. This eliminates the need to configure storage settings in
multiple places.

********
Overview
********

The ``atmosphere_storage`` variable organizes storage by purpose:

``images``
  Image storage for Glance. Supports multiple backends.

``volumes``
  Block storage for Cinder. Supports multiple backends.

``backup``
  Backup storage for Cinder backup.

``ephemeral``
  Ephemeral disk storage for Nova and libvirt.

The system automatically derives per-service Helm values from this single
variable for Cinder, Glance, Nova, libvirt, and Ceph Provisioners.

*********************
Default configuration
*********************

By default, Atmosphere configures image and volume storage to use the
integrated Ceph cluster, with local (qcow2) ephemeral disks for Nova.
The ``atmosphere_storage`` variable defaults to an empty dictionary
(``{}``), and the built-in defaults provide sensible starting values.

You can override any part of the configuration by setting
``atmosphere_storage`` in your inventory. Your overrides merge on top of
the built-in defaults using a recursive merge, so you only need to
specify the parts you want to change.

The built-in defaults are equivalent to:

.. code-block:: yaml

    images:
      default: rbd1
      backends:
        rbd1:
          type: rbd
          pool: glance.images
          replication: 3
          crush_rule: replicated_rule
          chunk_size: 8
          user: glance
    volumes:
      default: rbd1
      backends:
        rbd1:
          type: rbd
          pool: cinder.volumes
          replication: 3
          crush_rule: replicated_rule
          user: cinder
          secret_uuid: 457eb676-33da-42ec-9a8c-9293d545c337
    backup:
      type: rbd
      pool: cinder.backups
      replication: 3
      crush_rule: replicated_rule
      user: cinderbackup
    ephemeral:
      type: local

The integrated Ceph cluster works without additional configuration.

Using non-Ceph storage
======================

The built-in defaults include Ceph-backed ``rbd1`` entries for both
``images.backends`` and ``volumes.backends``. Because
``atmosphere_storage`` overrides merge recursively, defining a new backend
doesn't remove those defaults.

To replace the default Ceph backends with a non-Ceph layout, explicitly set
the inherited ``rbd1`` entries to ``null``. This keeps the storage
configuration on the non-Ceph path instead of running with both the default
Ceph backend and the new backend.

For a fully non-Ceph deployment:

1. Set ``images.default`` and ``volumes.default`` to your non-Ceph backends.
2. Set ``images.backends.rbd1: null`` and ``volumes.backends.rbd1: null``.
3. Set ``backup.type: none`` unless you want to keep Cinder backup on Ceph
   RBD.
4. Keep ``ephemeral.type: local`` unless you want Nova ephemeral disks on
   Ceph RBD.

.. code-block:: yaml

    atmosphere_storage:
      images:
        default: cinder_store
        backends:
          rbd1: null
          cinder_store:
            type: cinder
      volumes:
        default: powerstore
        backends:
          rbd1: null
          powerstore:
            type: powerstore
            address: 10.0.0.1
            username: admin
            password: secret
            protocol: iscsi
      backup:
        type: none
      ephemeral:
        type: local

Enabling RBD ephemeral storage
==============================

To use Ceph RBD for Nova ephemeral disks instead of local storage, set
the ``ephemeral`` section in your ``atmosphere_storage`` override:

.. code-block:: yaml

    atmosphere_storage:
      ephemeral:
        type: rbd
        pool: vms
        replication: 3
        crush_rule: replicated_rule
        user: cinder
        secret_uuid: 457eb676-33da-42ec-9a8c-9293d545c337

***********************
Supported backend types
***********************

Ceph RBD (``rbd``)
========================

Standard replicated Ceph RBD backend. Used for images, volumes, backups, and
ephemeral storage.

.. code-block:: yaml

    type: rbd
    pool: <pool_name>
    replication: 3
    crush_rule: replicated_rule
    user: <username>
    secret_uuid: <uuid>       # required for volumes and ephemeral

Ceph RBD erasure-coded (``rbd-ec``)
=========================================

Erasure-coded Ceph RBD backend for improved storage efficiency. Only supported
for volume backends. EC pools provide better storage utilization compared to
replicated pools, at the cost of slightly higher CPU overhead.

EC pools require two components:

1. A **metadata pool** (replicated) that stores metadata
2. A **data pool** (EC) that stores the actual volume data

.. code-block:: yaml

    type: rbd-ec
    pool: cinder.volumes.ec
    erasure_coded:
      k: 4                     # data chunks
      m: 2                     # coding (parity) chunks
      failure_domain: host
      device_class: hdd        # optional
    metadata_replication: 3
    crush_rule: replicated_rule  # optional: CRUSH rule for metadata pool
    user: cinder-ec       # must be unique per EC backend
    secret_uuid: <unique-uuid>

The EC pool configuration parameters are:

``k``
  Number of data chunks. Higher values provide better storage efficiency.

``m``
  Number of coding (parity) chunks. Higher values provide better fault
  tolerance.

``device_class``
  Target specific device types, for example ``hdd``, ``ssd``, or ``nvme``.

``failure_domain``
  Failure domain for data placement, for example ``host``, ``rack``, or
  ``room``.

``crush_rule``
  CRUSH rule for the replicated metadata pool. Defaults to
  ``replicated_rule``.

.. warning::

    Each erasure-coded backend requires a **dedicated** ``user`` and a
    **unique** ``secret_uuid``. Generate new UUID's with ``uuidgen``.

Dell PowerStore (``powerstore``)
================================

.. warning::

    Make sure that you set up the hosts inside of your storage array. They must
    **not** be inside a host group, or individual attachments won't work.

.. code-block:: yaml

    type: powerstore
    address: <management_ip_or_hostname>
    username: <username>
    password: <password>
    protocol: iscsi    # or fc

Pure storage (``pure``)
=======================

Pure Storage FlashArray integration. When using the NVMe protocol, you can
optionally set ``transport`` to ``roce`` or ``tcp``.

For additional options, see the `Cinder Pure Storage documentation
<https://docs.openstack.org/cinder/latest/configuration/block-storage/drivers/pure-storage-driver.html>`_.

.. code-block:: yaml

    type: pure
    protocol: iscsi    # or fc, nvme
    address: <management_ip_or_hostname>
    api_token: <token>
    transport: roce    # optional, only for nvme protocol

StorPool (``storpool``)
=======================

StorPool distributed storage backend. The system configures network settings
and file system mounts automatically.

.. code-block:: yaml

    type: storpool
    template: hybrid-2ssd

HPE Nimble storage (``nimble``)
===============================

HPE Nimble storage (including Alletra 5000/6000) integration with support for
iSCSI and Fibre Channel protocols.

For additional options, see the `Cinder HPE Nimble storage documentation
<https://docs.openstack.org/cinder/latest/configuration/block-storage/drivers/nimble-volume-driver.html>`_.

.. code-block:: yaml

    type: nimble
    protocol: iscsi    # or fc
    address: <management_ip_or_hostname>
    username: <username>
    password: <password>
    nimble_subnet_label: "*"  # optional

The ``nimble_subnet_label`` option defaults to ``"*"``.

Cinder (``cinder``)
====================

Cinder-backed Glance store. Only used for image backends.

.. code-block:: yaml

    type: cinder

Backup configuration
====================

The ``backup`` section controls Cinder backup storage. Atmosphere supports
these values:

``type: rbd``
  Store Cinder backups in Ceph. This is the built-in default.

``type: none``
  Disable the Cinder backup service and its storage-init job.

For non-Ceph volume backends such as PowerStore, Pure Storage, StorPool, or
Nimble, set ``backup.type: none`` unless you still plan to use Ceph for
backups.

If you keep Ceph backups while using a non-Ceph volume backend, define the
backup block explicitly:

.. code-block:: yaml

    atmosphere_storage:
      backup:
        type: rbd
        pool: cinder.backups
        replication: 3
        crush_rule: replicated_rule
        user: cinderbackup

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
            type: rbd-ec
            pool: cinder.volumes.ec
            erasure_coded:
              k: 4
              m: 2
              failure_domain: host
            metadata_replication: 3
            user: cinder-ec
            secret_uuid: 808c5658-7c46-4818-8f26-82a217e3a57a

The system automatically configures all required services: Cinder backend
configuration, Ceph pool creation, libvirt secret registration, and Ceph
client data pool routing.

Using Dell PowerStore
=====================

.. code-block:: yaml

    atmosphere_storage:
      images:
        default: cinder_store
        backends:
          rbd1: null
          cinder_store:
            type: cinder
      volumes:
        default: powerstore
        backends:
          rbd1: null
          powerstore:
            type: powerstore
            address: 10.0.0.1
            username: admin
            password: secret
            protocol: iscsi
      backup:
        type: none
      ephemeral:
        type: local

Using HPE Nimble storage
========================

.. code-block:: yaml

    atmosphere_storage:
      images:
        default: cinder_store
        backends:
          rbd1: null
          cinder_store:
            type: cinder
      volumes:
        default: nimble1
        backends:
          rbd1: null
          nimble1:
            type: nimble
            address: 10.0.0.1
            username: admin
            password: secret
            protocol: iscsi
            nimble_subnet_label: "*"
      backup:
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
            type: rbd
            pool: glance.images
            replication: 3
            user: glance
          cinder_store:
            type: cinder

*******************
Advanced overrides
*******************

The ``atmosphere_storage`` variable generates base Helm values. You can still
use per-service ``*_helm_values`` variables (such as ``cinder_helm_values`` or
``glance_helm_values``) to override specific settings. The per-service overrides
always take precedence.

*********************************************
Migrating from ``atmosphere_ceph_enabled``
*********************************************

The ``atmosphere_ceph_enabled`` variable is no longer supported. Storage
configuration now uses the unified ``atmosphere_storage`` variable. If your
inventory sets ``atmosphere_ceph_enabled``, remove it and configure
``atmosphere_storage`` instead.

If you previously set ``atmosphere_ceph_enabled: true``
=======================================================

No action beyond removing the variable is necessary. The built-in defaults
already configure Ceph RBD for images and volumes, which matches the
previous behavior.

.. code-block:: yaml

    # Remove this from your inventory:
    # atmosphere_ceph_enabled: true

If you previously set ``atmosphere_ceph_enabled: false``
========================================================

Remove the variable and configure ``atmosphere_storage`` to match your
environment. For example, if you use Dell PowerStore for volumes and local
ephemeral storage, make sure that you also null out the inherited ``rbd1``
backends:

.. code-block:: yaml

    # Remove this from your inventory:
    # atmosphere_ceph_enabled: false

    # Add this instead:
    atmosphere_storage:
      images:
        default: cinder_store
        backends:
          cinder_store:
            type: cinder
      volumes:
        default: powerstore
        backends:
          powerstore:
            type: powerstore
            address: 10.0.0.1
            username: admin
            password: secret
            protocol: iscsi
      backup:
        type: none
      ephemeral:
        type: local
