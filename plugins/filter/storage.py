# Copyright (c) 2025 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import os

from ansible.errors import AnsibleFilterError

DOCUMENTATION = """
  name: storage
  short_description: Derive per-service Helm values from atmosphere_storage
  version_added: 1.0.0
  description:
    - Filter plugins that convert a unified atmosphere_storage configuration
      into per-service Helm values for Cinder, Glance, Nova, Libvirt, and
      Ceph Provisioners.
  author:
    - VEXXHOST, Inc.
"""

_SCHEMA = None

_CEPH_TYPES = frozenset({"ceph_rbd", "ceph_rbd_ec"})
_NON_CEPH_TYPES = frozenset({"powerstore", "pure", "storpool"})


def _load_schema():
    global _SCHEMA
    if _SCHEMA is None:
        schema_path = os.path.join(
            os.path.dirname(__file__), "schemas", "storage.json"
        )
        with open(schema_path) as f:
            _SCHEMA = json.load(f)
    return _SCHEMA


def validate_storage(storage):
    """Validate atmosphere_storage against JSON Schema."""
    try:
        import jsonschema
    except ImportError:
        raise AnsibleFilterError(
            "jsonschema is required for storage validation. "
            "Install it with: pip install jsonschema"
        )

    schema = _load_schema()
    try:
        jsonschema.validate(instance=storage, schema=schema)
    except jsonschema.ValidationError as e:
        path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        raise AnsibleFilterError(
            f"atmosphere_storage validation error at '{path}': {e.message}"
        )
    return storage


def _get_volume_backends(storage):
    """Get the volume backends dict from storage config."""
    return storage.get("volumes", {}).get("backends", {})


def _has_any_ceph_volume_backend(storage):
    """Check if any volume backend uses Ceph."""
    return any(
        b.get("type") in _CEPH_TYPES for b in _get_volume_backends(storage).values()
    )


def _has_any_non_ceph_volume_backend(storage):
    """Check if any volume backend is non-Ceph (requires iSCSI/device access)."""
    return any(
        b.get("type") in _NON_CEPH_TYPES
        for b in _get_volume_backends(storage).values()
    )


def _ceph_rbd_cinder_backend(name, backend):
    """Generate Cinder backend config for a Ceph RBD backend (replicated or EC)."""
    config = {
        "volume_driver": "cinder.volume.drivers.rbd.RBDDriver",
        "volume_backend_name": name,
        "rbd_pool": backend["pool"],
        "rbd_ceph_conf": "/etc/ceph/ceph.conf",
        "rbd_flatten_volume_from_snapshot": False,
        "report_discard_supported": True,
        "rbd_max_clone_depth": 5,
        "rbd_store_chunk_size": 4,
        "rados_connect_timeout": -1,
        "rbd_user": backend["ceph_user"],
        "rbd_secret_uuid": backend["secret_uuid"],
        "image_volume_cache_enabled": True,
        "image_volume_cache_max_size_gb": 200,
        "image_volume_cache_max_count": 50,
    }
    if backend["type"] == "ceph_rbd_ec":
        config["rbd_data_pool"] = backend.get(
            "data_pool_name", f"{backend['pool']}.data"
        )
    return config


def _powerstore_cinder_backend(name, backend):
    """Generate Cinder backend config for PowerStore."""
    return {
        "volume_backend_name": name,
        "volume_driver": "cinder.volume.drivers.dell_emc.powerstore.driver.PowerStoreDriver",
        "san_ip": backend["san_ip"],
        "san_login": backend["san_login"],
        "san_password": backend["san_password"],
        "storage_protocol": backend["storage_protocol"],
    }


def _pure_cinder_backend(name, backend):
    """Generate Cinder backend config for Pure Storage."""
    config = {
        "volume_backend_name": name,
        "volume_driver": backend["volume_driver"],
        "san_ip": backend["san_ip"],
        "pure_api_token": backend["pure_api_token"],
        "use_multipath_for_image_xfer": True,
        "pure_eradicate_on_delete": True,
    }
    if "pure_nvme_transport" in backend:
        config["pure_nvme_transport"] = backend["pure_nvme_transport"]
    return config


def _storpool_cinder_backend(name, backend):
    """Generate Cinder backend config for StorPool."""
    return {
        "volume_backend_name": name,
        "volume_driver": "cinder.volume.drivers.storpool.StorPoolDriver",
        "storpool_template": backend["storpool_template"],
        "report_discard_supported": True,
    }


_CINDER_BACKEND_GENERATORS = {
    "ceph_rbd": _ceph_rbd_cinder_backend,
    "ceph_rbd_ec": _ceph_rbd_cinder_backend,
    "powerstore": _powerstore_cinder_backend,
    "pure": _pure_cinder_backend,
    "storpool": _storpool_cinder_backend,
}

_NON_CEPH_INIT_JOBS = [
    "cinder-db-sync",
    "cinder-ks-user",
    "cinder-ks-endpoints",
    "cinder-rabbit-init",
]
_NON_CEPH_DEPENDENCIES = {
    "static": {
        name: {"jobs": list(_NON_CEPH_INIT_JOBS)}
        for name in ("api", "scheduler", "volume", "volume_usage_audit")
    }
}


def _generate_cinder_pools(backends_config):
    """Generate Ceph pool definitions from volume backend configuration."""
    pools = {}
    for name, backend in backends_config.items():
        if backend["type"] == "ceph_rbd":
            pools[backend["pool"]] = {
                "replication": backend.get("replication", 3),
                "crush_rule": backend.get("crush_rule", "replicated_rule"),
                "chunk_size": backend.get("chunk_size", 8),
                "app_name": "cinder-volume",
            }
        elif backend["type"] == "ceph_rbd_ec":
            ec = backend["erasure_coded"]
            pool_config = {
                "app_name": "cinder-volume",
                "erasure_coded": {
                    "k": ec["k"],
                    "m": ec["m"],
                    "failure_domain": ec["failure_domain"],
                },
                "metadata": {
                    "replication": backend.get("metadata_replication", 3),
                },
            }
            if ec.get("device_class"):
                pool_config["erasure_coded"]["device_class"] = ec["device_class"]
            data_pool_name = backend.get("data_pool_name")
            if data_pool_name:
                pool_config["erasure_coded"]["data_pool_name"] = data_pool_name
            pools[backend["pool"]] = pool_config
    return pools


def _apply_vendor_pod_config(result, backends_config):
    """Apply vendor-specific pod configuration for StorPool and Pure backends."""
    if any(b["type"] == "storpool" for b in backends_config.values()):
        result.setdefault("pod", {})
        result["pod"]["useHostNetwork"] = {"volume": True}
        result["pod"]["mounts"] = {
            "cinder_volume": {
                "volumeMounts": [
                    {
                        "name": "etc-storpool-conf",
                        "mountPath": "/etc/storpool.conf",
                        "readOnly": True,
                    },
                    {
                        "name": "etc-storpool-conf-d",
                        "mountPath": "/etc/storpool.conf.d",
                        "readOnly": True,
                    },
                ],
                "volumes": [
                    {
                        "name": "etc-storpool-conf",
                        "hostPath": {"type": "File", "path": "/etc/storpool.conf"},
                    },
                    {
                        "name": "etc-storpool-conf-d",
                        "hostPath": {
                            "type": "Directory",
                            "path": "/etc/storpool.conf.d",
                        },
                    },
                ],
            }
        }

    if any(b["type"] == "pure" for b in backends_config.values()):
        result.setdefault("pod", {})
        result["pod"]["useHostNetwork"] = {"volume": True, "backup": True}
        result["pod"]["security_context"] = {
            "cinder_volume": {
                "container": {
                    "cinder_volume": {
                        "readOnlyRootFilesystem": True,
                        "privileged": True,
                    }
                }
            },
            "cinder_backup": {
                "container": {
                    "cinder_backup": {"privileged": True}
                }
            },
        }


def storage_to_cinder_helm_values(storage):
    """Derive Cinder Helm values from atmosphere_storage."""
    validate_storage(storage)

    volumes = storage.get("volumes", {})
    backups = storage.get("backups", {})
    default_backend = volumes.get("default")
    backends_config = volumes.get("backends", {})

    result = {}

    # Determine storage type for the chart
    has_ceph = _has_any_ceph_volume_backend(storage)
    has_non_ceph = _has_any_non_ceph_volume_backend(storage)

    if has_ceph:
        result["storage"] = "ceph"
    elif has_non_ceph:
        first_type = next(
            b["type"] for b in backends_config.values()
            if b["type"] in _NON_CEPH_TYPES
        )
        result["storage"] = first_type

    # Generate backends
    backends = {}
    for name, backend in backends_config.items():
        generator = _CINDER_BACKEND_GENERATORS.get(backend["type"])
        if generator:
            backends[name] = generator(name, backend)

    pools = _generate_cinder_pools(backends_config)

    result["conf"] = {
        "backends": backends,
        "cinder": {
            "DEFAULT": {
                "enabled_backends": ",".join(backends_config.keys()),
                "default_volume_type": default_backend,
            }
        },
    }

    if pools:
        result["conf"]["ceph"] = {"pools": pools}

    # Backup configuration
    if backups.get("type") == "ceph_rbd":
        result["conf"]["cinder"]["DEFAULT"]["backup_driver"] = (
            "cinder.backup.drivers.ceph.CephBackupDriver"
        )
        result["conf"]["cinder"]["DEFAULT"]["backup_ceph_conf"] = "/etc/ceph/ceph.conf"
        result["conf"]["cinder"]["DEFAULT"]["backup_ceph_user"] = backups["ceph_user"]
        result["conf"]["cinder"]["DEFAULT"]["backup_ceph_pool"] = backups["pool"]

        result["conf"].setdefault("ceph", {}).setdefault("pools", {})
        result["conf"]["ceph"]["pools"]["backup"] = {
            "replication": backups.get("replication", 3),
            "crush_rule": backups.get("crush_rule", "replicated_rule"),
            "chunk_size": backups.get("chunk_size", 8),
            "app_name": "cinder-backup",
        }
    elif backups.get("type") == "none":
        result["manifests"] = {
            "deployment_backup": False,
            "job_backup_storage_init": False,
        }

    # Enable iSCSI/device access for non-Ceph backends
    if has_non_ceph:
        result["conf"]["enable_iscsi"] = True
        result["dependencies"] = _NON_CEPH_DEPENDENCIES

        if not has_ceph:
            result.setdefault("manifests", {})
            result["manifests"]["job_storage_init"] = False

    _apply_vendor_pod_config(result, backends_config)

    return result


def _glance_store_type(backend_type):
    """Map atmosphere backend type to Glance store type string."""
    mapping = {
        "ceph_rbd": "rbd",
        "cinder": "cinder",
    }
    return mapping.get(backend_type, backend_type)


def _glance_backend_config(backend, include_pool_settings=False):
    """Generate per-backend Glance config section.

    When ``include_pool_settings`` is True, pool-level settings (replication,
    crush_rule) are included.  This is used for the legacy single-backend
    ``glance_store`` path which embeds them directly.
    """
    if backend["type"] == "ceph_rbd":
        config = {
            "rbd_store_pool": backend["pool"],
            "rbd_store_user": backend["ceph_user"],
            "rbd_store_ceph_conf": "/etc/ceph/ceph.conf",
            "rbd_store_chunk_size": backend.get("chunk_size", 8),
        }
        if include_pool_settings:
            config["rbd_store_replication"] = backend.get("replication", 3)
            config["rbd_store_crush_rule"] = backend.get(
                "crush_rule", "replicated_rule"
            )
        return config
    elif backend["type"] == "cinder":
        return {
            "cinder_catalog_info": "volumev3::internalURL",
        }
    return {}


def storage_to_glance_helm_values(storage):
    """Derive Glance Helm values from atmosphere_storage."""
    validate_storage(storage)

    images = storage.get("images", {})
    default_backend = images.get("default")
    backends_config = images.get("backends", {})

    result = {}

    has_ceph = any(
        b.get("type") == "ceph_rbd" for b in backends_config.values()
    )
    has_cinder = any(
        b.get("type") == "cinder" for b in backends_config.values()
    )

    if has_ceph:
        result["storage"] = "rbd"

    glance_conf = {}

    if len(backends_config) > 1:
        # Multi-backend: use enabled_backends
        enabled_parts = []
        for name, backend in backends_config.items():
            store_type = _glance_store_type(backend["type"])
            enabled_parts.append(f"{name}:{store_type}")

        glance_conf["DEFAULT"] = {
            "enabled_backends": ",".join(enabled_parts),
        }
        glance_conf["glance_store"] = {
            "default_backend": default_backend,
        }

        for name, backend in backends_config.items():
            glance_conf[name] = _glance_backend_config(backend)
    else:
        # Single backend: use legacy glance_store config
        for name, backend in backends_config.items():
            if backend["type"] == "ceph_rbd":
                glance_conf["glance_store"] = _glance_backend_config(
                    backend, include_pool_settings=True
                )

    if glance_conf:
        result["conf"] = {"glance": glance_conf}

    # Security context for Cinder store
    if has_cinder:
        result.setdefault("pod", {})
        result["pod"]["security_context"] = {
            "glance": {
                "container": {
                    "glance_api": {
                        "allowPrivilegeEscalation": True,
                        "readOnlyRootFilesystem": False,
                        "privileged": True,
                        "capabilities": {"add": ["SYS_ADMIN"]},
                    }
                }
            }
        }
        result["pod"]["useHostNetwork"] = {"api": True}

    return result


def storage_to_nova_helm_values(storage):
    """Derive Nova Helm values from atmosphere_storage."""
    validate_storage(storage)

    ephemeral = storage.get("ephemeral", {})
    result = {}

    if ephemeral.get("type") == "ceph_rbd":
        result["conf"] = {
            "ceph": {"enabled": True},
            "nova": {
                "libvirt": {
                    "images_type": "rbd",
                    "images_rbd_pool": ephemeral["pool"],
                    "images_rbd_ceph_conf": "/etc/ceph/ceph.conf",
                    "rbd_user": ephemeral["ceph_user"],
                    "rbd_secret_uuid": ephemeral["secret_uuid"],
                }
            },
        }
    elif ephemeral.get("type") == "local":
        result["conf"] = {
            "ceph": {"enabled": False},
            "nova": {
                "libvirt": {
                    "images_type": "qcow2",
                }
            },
        }

    # Enable iSCSI if any volume backend needs it
    if _has_any_non_ceph_volume_backend(storage):
        result.setdefault("conf", {})
        result["conf"]["enable_iscsi"] = True

    return result


def storage_to_libvirt_helm_values(storage):
    """Derive Libvirt Helm values from atmosphere_storage."""
    validate_storage(storage)

    volumes = storage.get("volumes", {})
    ephemeral = storage.get("ephemeral", {})
    default_backend_name = volumes.get("default")
    backends_config = volumes.get("backends", {})

    result = {}

    has_ceph = (
        _has_any_ceph_volume_backend(storage)
        or ephemeral.get("type") == "ceph_rbd"
    )

    ceph_conf = {"enabled": has_ceph}

    if has_ceph:
        default_backend = backends_config.get(default_backend_name, {})
        if default_backend.get("type") in _CEPH_TYPES:
            ceph_conf["cinder"] = {
                "user": default_backend["ceph_user"],
                "secret_uuid": default_backend["secret_uuid"],
            }

        additional_users = []
        for name, backend in backends_config.items():
            if name == default_backend_name:
                continue
            if backend.get("type") in _CEPH_TYPES:
                additional_users.append(
                    {
                        "user": backend["ceph_user"],
                        "secret_uuid": backend["secret_uuid"],
                        "secret_name": f"cinder-volume-rbd-keyring-{name}",
                    }
                )

        if additional_users:
            ceph_conf["additional_users"] = additional_users

    result["conf"] = {"ceph": ceph_conf}

    return result


def storage_to_ceph_provisioners_helm_values(storage):
    """Derive Ceph Provisioners Helm values from atmosphere_storage."""
    validate_storage(storage)

    backends_config = _get_volume_backends(storage)

    client_conf = {}
    for name, backend in backends_config.items():
        if backend.get("type") == "ceph_rbd_ec":
            data_pool = backend.get("data_pool_name", f"{backend['pool']}.data")
            client_key = f"client.{backend['ceph_user']}"
            client_conf[client_key] = {
                "rbd default data pool": data_pool,
            }

    result = {}
    if client_conf:
        result["conf"] = {"ceph": client_conf}

    return result


class FilterModule(object):
    def filters(self):
        return {
            "validate_storage": validate_storage,
            "storage_to_cinder_helm_values": storage_to_cinder_helm_values,
            "storage_to_glance_helm_values": storage_to_glance_helm_values,
            "storage_to_nova_helm_values": storage_to_nova_helm_values,
            "storage_to_libvirt_helm_values": storage_to_libvirt_helm_values,
            "storage_to_ceph_provisioners_helm_values": storage_to_ceph_provisioners_helm_values,
        }
