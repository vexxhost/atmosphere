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

from __future__ import annotations

from typing import Annotated, Any, Callable, ClassVar, Literal, Self, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RbdPoolSpec(_StrictBase):
    pool: str = Field(description="Ceph RBD pool name.")
    crush_rule: str = Field(
        default="replicated_rule",
        description="CRUSH rule applied to the pool.",
    )
    ceph_user: str = Field(description="Ceph client user name.")
    chunk_size: int = Field(
        default=8, description="RBD stripe unit size in MiB."
    )


class ReplicatedRbdPoolSpec(RbdPoolSpec):
    replication: int = Field(
        default=3, description="Number of replicas for the pool."
    )


class ErasureCodedSpec(_StrictBase):
    k: int = Field(ge=2, description="Number of data chunks.")
    m: int = Field(ge=1, description="Number of coding (parity) chunks.")
    failure_domain: str = Field(
        description="CRUSH failure domain (e.g. 'host', 'rack')."
    )
    device_class: str | None = Field(
        default=None,
        description="CRUSH device class to restrict placement (e.g. 'ssd').",
    )

    @model_validator(mode="after")
    def _validate_coding_params(self) -> Self:
        if self.m >= self.k:
            raise ValueError(
                f"m ({self.m}) must be less than k ({self.k})"
            )
        return self


class ErasureCodedRbdPoolSpec(RbdPoolSpec):
    data_pool: str | None = Field(
        default=None,
        description="Override name for the EC data pool (default: '<pool>.data').",
    )
    erasure_coded: ErasureCodedSpec = Field(
        description="Erasure coding profile parameters."
    )
    metadata_replication: int = Field(
        ge=1, description="Replication factor for the metadata pool."
    )


class LibvirtSecretSpec(_StrictBase):
    secret_uuid: UUID = Field(
        description="UUID of the libvirt secret used for Ceph authentication."
    )


# -- Image backends --


class ImageBackendRbd(ReplicatedRbdPoolSpec):
    type: Literal["rbd"]


class ImageBackendCinder(_StrictBase):
    type: Literal["cinder"]


ImageBackend = Annotated[
    Union[ImageBackendRbd, ImageBackendCinder],
    Field(discriminator="type"),
]


# -- Volume backends --


class VolumeBackendRbd(ReplicatedRbdPoolSpec, LibvirtSecretSpec):
    type: Literal["rbd"]
    host_attached: ClassVar[bool] = False
    cinder_driver: ClassVar[str] = "cinder.volume.drivers.rbd.RBDDriver"


class VolumeBackendRbdEc(ErasureCodedRbdPoolSpec, LibvirtSecretSpec):
    type: Literal["rbd-ec"]
    host_attached: ClassVar[bool] = False
    cinder_driver: ClassVar[str] = "cinder.volume.drivers.rbd.RBDDriver"


class VolumeBackendPowerstore(_StrictBase):
    type: Literal["powerstore"]
    host_attached: ClassVar[bool] = True
    cinder_driver: ClassVar[str] = (
        "cinder.volume.drivers.dell_emc.powerstore.driver.PowerStoreDriver"
    )
    ip: str = Field(description="PowerStore management IP address.")
    login: str = Field(description="PowerStore management login.")
    password: str = Field(description="PowerStore management password.")
    protocol: Literal["fc", "iscsi"] = Field(
        description="Storage transport protocol."
    )


class _VolumeBackendPureBase(_StrictBase):
    type: Literal["pure"]
    host_attached: ClassVar[bool] = True
    ip: str = Field(description="Pure Storage management IP address.")
    api_token: str = Field(description="Pure Storage API token.")


class VolumeBackendPureISCSI(_VolumeBackendPureBase):
    protocol: Literal["iscsi"]
    cinder_driver: ClassVar[str] = "cinder.volume.drivers.pure.PureISCSIDriver"


class VolumeBackendPureFC(_VolumeBackendPureBase):
    protocol: Literal["fc"]
    cinder_driver: ClassVar[str] = "cinder.volume.drivers.pure.PureFCDriver"


class VolumeBackendPureNVME(_VolumeBackendPureBase):
    protocol: Literal["nvme"]
    cinder_driver: ClassVar[str] = "cinder.volume.drivers.pure.PureNVMEDriver"
    transport: Literal["roce", "tcp"] | None = Field(
        default=None, description="NVMe transport type."
    )


VolumeBackendPure = Annotated[
    Union[VolumeBackendPureISCSI, VolumeBackendPureFC, VolumeBackendPureNVME],
    Field(discriminator="protocol"),
]


class VolumeBackendStorpool(_StrictBase):
    type: Literal["storpool"]
    host_attached: ClassVar[bool] = True
    cinder_driver: ClassVar[str] = (
        "cinder.volume.drivers.storpool.StorPoolDriver"
    )
    template: str = Field(description="StorPool volume template name.")


VolumeBackend = Annotated[
    Union[
        VolumeBackendRbd,
        VolumeBackendRbdEc,
        VolumeBackendPowerstore,
        VolumeBackendPure,
        VolumeBackendStorpool,
    ],
    Field(discriminator="type"),
]

# -- Backup backends --


class BackupBackendRbd(ReplicatedRbdPoolSpec):
    type: Literal["rbd"]


class BackupBackendNone(_StrictBase):
    type: Literal["none"]


BackupBackend = Annotated[
    Union[BackupBackendRbd, BackupBackendNone],
    Field(discriminator="type"),
]

# -- Ephemeral backends --


class EphemeralBackendRbd(ReplicatedRbdPoolSpec, LibvirtSecretSpec):
    type: Literal["rbd"]


class EphemeralBackendLocal(_StrictBase):
    type: Literal["local"]


EphemeralBackend = Annotated[
    Union[EphemeralBackendRbd, EphemeralBackendLocal],
    Field(discriminator="type"),
]


# -- Top-level configuration --


class ImageStorageConfig(_StrictBase):
    default: str = Field(description="Name of the default image backend.")
    backends: dict[str, ImageBackend] = Field(
        min_length=1, description="Mapping of backend name to image backend config."
    )

    @model_validator(mode="after")
    def _validate_default_in_backends(self) -> Self:
        if self.default not in self.backends:
            raise ValueError(
                f"default {self.default!r} is not in backends: {list(self.backends)}"
            )
        return self


class VolumeStorageConfig(_StrictBase):
    default: str = Field(description="Name of the default volume backend.")
    backends: dict[str, VolumeBackend] = Field(
        min_length=1, description="Mapping of backend name to volume backend config."
    )

    @model_validator(mode="after")
    def _validate_default_in_backends(self) -> Self:
        if self.default not in self.backends:
            raise ValueError(
                f"default {self.default!r} is not in backends: {list(self.backends)}"
            )
        return self


class StorageConfig(_StrictBase):
    """Top-level storage configuration for Atmosphere.

    Example::

        images:
          default: rbd1
          backends:
            rbd1:
              type: rbd
              pool: glance.images
              ceph_user: glance
        volumes:
          default: rbd1
          backends:
            rbd1:
              type: rbd
              pool: cinder.volumes
              ceph_user: cinder
              secret_uuid: 457eb676-33da-42ec-9a8c-9293d545c337
        backups:
          type: rbd
          pool: cinder.backups
          ceph_user: cinderbackup
        ephemeral:
          type: rbd
          pool: vms
          ceph_user: cinder
          secret_uuid: 457eb676-33da-42ec-9a8c-9293d545c337
    """

    images: ImageStorageConfig | None = Field(
        default=None, description="Glance image storage configuration."
    )
    volumes: VolumeStorageConfig | None = Field(
        default=None, description="Cinder volume storage configuration."
    )
    backups: BackupBackend | None = Field(
        default=None, description="Cinder backup backend configuration."
    )
    ephemeral: EphemeralBackend | None = Field(
        default=None, description="Nova ephemeral disk backend configuration."
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

HelmValues = dict[str, Any]

CinderAmender = Callable[..., None]
GlanceAmender = Callable[..., None]

def _parse(raw: Any) -> StorageConfig:
    """Validate and parse raw Ansible input into a StorageConfig."""
    return StorageConfig.model_validate(raw)


# -- Cinder per-backend config generators --


def _ceph_rbd_cinder_backend(
    name: str,
    backend: VolumeBackendRbd | VolumeBackendRbdEc,
) -> dict[str, Any]:
    """Generate Cinder backend config for a Ceph RBD backend (replicated or EC)."""
    config: dict[str, Any] = {
        "volume_driver": backend.cinder_driver,
        "volume_backend_name": name,
        "rbd_pool": backend.pool,
        "rbd_ceph_conf": "/etc/ceph/ceph.conf",
        "rbd_flatten_volume_from_snapshot": False,
        "report_discard_supported": True,
        "rbd_max_clone_depth": 5,
        "rbd_store_chunk_size": backend.chunk_size,
        "rados_connect_timeout": -1,
        "rbd_user": backend.ceph_user,
        "rbd_secret_uuid": str(backend.secret_uuid),
        "image_volume_cache_enabled": True,
        "image_volume_cache_max_size_gb": 200,
        "image_volume_cache_max_count": 50,
    }
    if isinstance(backend, VolumeBackendRbdEc):
        config["rbd_data_pool"] = (
            backend.data_pool
            if backend.data_pool
            else f"{backend.pool}.data"
        )
    return config


_POWERSTORE_PROTOCOL_MAP: dict[str, str] = {
    "fc": "FC",
    "iscsi": "iSCSI",
}


def _powerstore_cinder_backend(
    name: str, backend: VolumeBackendPowerstore
) -> dict[str, Any]:
    """Generate Cinder backend config for PowerStore."""
    return {
        "volume_backend_name": name,
        "volume_driver": backend.cinder_driver,
        "san_ip": backend.ip,
        "san_login": backend.login,
        "san_password": backend.password,
        "storage_protocol": _POWERSTORE_PROTOCOL_MAP[backend.protocol],
    }


def _pure_cinder_backend(
    name: str,
    backend: VolumeBackendPureISCSI | VolumeBackendPureFC | VolumeBackendPureNVME,
) -> dict[str, Any]:
    """Generate Cinder backend config for Pure Storage."""
    config: dict[str, Any] = {
        "volume_backend_name": name,
        "volume_driver": backend.cinder_driver,
        "san_ip": backend.ip,
        "pure_api_token": backend.api_token,
        "use_multipath_for_image_xfer": True,
        "pure_eradicate_on_delete": True,
    }
    if isinstance(backend, VolumeBackendPureNVME) and backend.transport is not None:
        config["pure_nvme_transport"] = backend.transport
    return config


def _storpool_cinder_backend(
    name: str, backend: VolumeBackendStorpool
) -> dict[str, Any]:
    """Generate Cinder backend config for StorPool."""
    return {
        "volume_backend_name": name,
        "volume_driver": backend.cinder_driver,
        "storpool_template": backend.template,
        "report_discard_supported": True,
    }


_NON_CEPH_INIT_JOBS: list[str] = [
    "cinder-db-sync",
    "cinder-ks-user",
    "cinder-ks-endpoints",
    "cinder-rabbit-init",
]
_NON_CEPH_DEPENDENCIES: dict[str, Any] = {
    "static": {
        name: {"jobs": list(_NON_CEPH_INIT_JOBS)}
        for name in ("api", "scheduler", "volume", "volume_usage_audit")
    }
}


# -- Cinder amend functions --


def _amend_cinder_rbd(result: HelmValues, name: str, backend: VolumeBackendRbd) -> None:
    """Amend Cinder result for an rbd volume backend."""
    result["storage"] = "ceph"
    result["conf"]["backends"][name] = _ceph_rbd_cinder_backend(name, backend)
    pools = result["conf"].setdefault("ceph", {}).setdefault("pools", {})
    pools[backend.pool] = {
        "replication": backend.replication,
        "crush_rule": backend.crush_rule,
        "chunk_size": backend.chunk_size,
        "app_name": "cinder-volume",
    }


def _amend_cinder_rbd_ec(result: HelmValues, name: str, backend: VolumeBackendRbdEc) -> None:
    """Amend Cinder result for an rbd-ec volume backend."""
    result["storage"] = "ceph"
    result["conf"]["backends"][name] = _ceph_rbd_cinder_backend(name, backend)
    pools = result["conf"].setdefault("ceph", {}).setdefault("pools", {})
    ec = backend.erasure_coded
    pool_config: dict[str, Any] = {
        "app_name": "cinder-volume",
        "erasure_coded": {
            "k": ec.k,
            "m": ec.m,
            "failure_domain": ec.failure_domain,
        },
        "metadata": {
            "replication": backend.metadata_replication,
        },
    }
    if ec.device_class is not None:
        pool_config["erasure_coded"]["device_class"] = ec.device_class
    if backend.data_pool is not None:
        pool_config["erasure_coded"]["data_pool_name"] = backend.data_pool
    pools[backend.pool] = pool_config


def _amend_cinder_non_ceph(
    result: HelmValues,
    name: str,
    backend: VolumeBackendPowerstore | VolumeBackendPureISCSI | VolumeBackendPureFC | VolumeBackendPureNVME | VolumeBackendStorpool,
) -> None:
    """Common amendments for non-Ceph volume backends."""
    result.setdefault("storage", backend.type)
    result["conf"]["enable_iscsi"] = True
    result["dependencies"] = _NON_CEPH_DEPENDENCIES


def _amend_cinder_powerstore(result: HelmValues, name: str, backend: VolumeBackendPowerstore) -> None:
    """Amend Cinder result for a PowerStore volume backend."""
    _amend_cinder_non_ceph(result, name, backend)
    result["conf"]["backends"][name] = _powerstore_cinder_backend(name, backend)


def _amend_cinder_pure(
    result: HelmValues,
    name: str,
    backend: VolumeBackendPureISCSI | VolumeBackendPureFC | VolumeBackendPureNVME,
) -> None:
    """Amend Cinder result for a Pure Storage volume backend."""
    _amend_cinder_non_ceph(result, name, backend)
    result["conf"]["backends"][name] = _pure_cinder_backend(name, backend)
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


def _amend_cinder_storpool(result: HelmValues, name: str, backend: VolumeBackendStorpool) -> None:
    """Amend Cinder result for a StorPool volume backend."""
    _amend_cinder_non_ceph(result, name, backend)
    result["conf"]["backends"][name] = _storpool_cinder_backend(name, backend)
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


_CINDER_AMENDERS: dict[str, CinderAmender] = {
    "rbd": _amend_cinder_rbd,
    "rbd-ec": _amend_cinder_rbd_ec,
    "powerstore": _amend_cinder_powerstore,
    "pure": _amend_cinder_pure,
    "storpool": _amend_cinder_storpool,
}


def _amend_cinder_backup(
    result: HelmValues, backups: BackupBackendRbd | BackupBackendNone | None
) -> None:
    """Amend Cinder result with backup configuration."""
    if isinstance(backups, BackupBackendRbd):
        result["conf"]["cinder"]["DEFAULT"]["backup_driver"] = (
            "cinder.backup.drivers.ceph.CephBackupDriver"
        )
        result["conf"]["cinder"]["DEFAULT"]["backup_ceph_conf"] = "/etc/ceph/ceph.conf"
        result["conf"]["cinder"]["DEFAULT"]["backup_ceph_user"] = backups.ceph_user
        result["conf"]["cinder"]["DEFAULT"]["backup_ceph_pool"] = backups.pool

        pools = result["conf"].setdefault("ceph", {}).setdefault("pools", {})
        pools["backup"] = {
            "replication": backups.replication,
            "crush_rule": backups.crush_rule,
            "chunk_size": backups.chunk_size,
            "app_name": "cinder-backup",
        }
    elif isinstance(backups, BackupBackendNone):
        result.setdefault("manifests", {})
        result["manifests"]["deployment_backup"] = False
        result["manifests"]["job_backup_storage_init"] = False


def storage_to_cinder_helm_values(raw: Any) -> HelmValues:
    """Derive Cinder Helm values from atmosphere_storage."""

    storage = _parse(raw)
    volumes = storage.volumes
    backups = storage.backups
    default_backend = volumes.default if volumes else None
    backends_config = volumes.backends if volumes else {}

    result: HelmValues = {"conf": {"backends": {}, "cinder": {"DEFAULT": {}}}}

    for name, backend in backends_config.items():
        _CINDER_AMENDERS[backend.type](result, name, backend)

    result["conf"]["cinder"]["DEFAULT"]["enabled_backends"] = ",".join(
        backends_config.keys()
    )
    result["conf"]["cinder"]["DEFAULT"]["default_volume_type"] = default_backend

    _amend_cinder_backup(result, backups)

    # Disable storage init when only non-Ceph volume backends are present
    if result["conf"].get("enable_iscsi") and result.get("storage") != "ceph":
        result.setdefault("manifests", {})
        result["manifests"]["job_storage_init"] = False

    return result


# -- Glance helpers --


def _glance_store_type(backend_type: str) -> str:
    """Map atmosphere backend type to Glance store type string."""
    mapping = {
        "rbd": "rbd",
        "cinder": "cinder",
    }
    return mapping.get(backend_type, backend_type)


def _glance_backend_config(
    backend: ImageBackendRbd | ImageBackendCinder,
    include_pool_settings: bool = False,
) -> dict[str, Any]:
    """Generate per-backend Glance config section.

    When ``include_pool_settings`` is True, pool-level settings (replication,
    crush_rule) are included.  This is used for the legacy single-backend
    ``glance_store`` path which embeds them directly.
    """
    if isinstance(backend, ImageBackendRbd):
        config: dict[str, Any] = {
            "rbd_store_pool": backend.pool,
            "rbd_store_user": backend.ceph_user,
            "rbd_store_ceph_conf": "/etc/ceph/ceph.conf",
            "rbd_store_chunk_size": backend.chunk_size,
        }
        if include_pool_settings:
            config["rbd_store_replication"] = backend.replication
            config["rbd_store_crush_rule"] = backend.crush_rule
        return config
    elif isinstance(backend, ImageBackendCinder):
        return {
            "cinder_catalog_info": "volumev3::internalURL",
        }
    return {}


# -- Glance amend functions --


def _amend_glance_rbd(
    result: HelmValues, name: str, backend: ImageBackendRbd, multi_backend: bool
) -> None:
    """Amend Glance result for an rbd backend."""
    result["storage"] = "rbd"
    glance = result["conf"]["glance"]
    if multi_backend:
        glance[name] = _glance_backend_config(backend)
    else:
        glance["glance_store"] = _glance_backend_config(
            backend, include_pool_settings=True
        )


def _amend_glance_cinder(
    result: HelmValues, name: str, backend: ImageBackendCinder, multi_backend: bool
) -> None:
    """Amend Glance result for a cinder backend."""
    if multi_backend:
        result["conf"]["glance"][name] = _glance_backend_config(backend)

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


_GLANCE_AMENDERS: dict[str, GlanceAmender] = {
    "rbd": _amend_glance_rbd,
    "cinder": _amend_glance_cinder,
}


def storage_to_glance_helm_values(raw: Any) -> HelmValues:
    """Derive Glance Helm values from atmosphere_storage."""

    storage = _parse(raw)
    images = storage.images
    default_backend = images.default if images else None
    backends_config = images.backends if images else {}

    result: HelmValues = {"conf": {"glance": {}}}
    multi_backend = len(backends_config) > 1

    if multi_backend:
        enabled_parts: list[str] = []
        for name, backend in backends_config.items():
            store_type = _glance_store_type(backend.type)
            enabled_parts.append(f"{name}:{store_type}")

        result["conf"]["glance"]["DEFAULT"] = {
            "enabled_backends": ",".join(enabled_parts),
        }
        result["conf"]["glance"]["glance_store"] = {
            "default_backend": default_backend,
        }

    for name, backend in backends_config.items():
        _GLANCE_AMENDERS[backend.type](result, name, backend, multi_backend)

    if not result["conf"]["glance"]:
        del result["conf"]

    return result


def storage_to_nova_helm_values(raw: Any) -> HelmValues:
    """Derive Nova Helm values from atmosphere_storage."""

    storage = _parse(raw)
    ephemeral = storage.ephemeral
    result: HelmValues = {}

    if isinstance(ephemeral, EphemeralBackendRbd):
        result["conf"] = {
            "ceph": {"enabled": True},
            "nova": {
                "libvirt": {
                    "images_type": "rbd",
                    "images_rbd_pool": ephemeral.pool,
                    "images_rbd_ceph_conf": "/etc/ceph/ceph.conf",
                    "rbd_user": ephemeral.ceph_user,
                    "rbd_secret_uuid": str(ephemeral.secret_uuid),
                }
            },
        }
    elif isinstance(ephemeral, EphemeralBackendLocal):
        result["conf"] = {
            "ceph": {"enabled": False},
            "nova": {
                "libvirt": {
                    "images_type": "qcow2",
                }
            },
        }

    # Amend for volume backends that attach block devices to the host
    volumes = storage.volumes
    if volumes:
        for backend in volumes.backends.values():
            if backend.host_attached:
                result.setdefault("conf", {})
                result["conf"]["enable_iscsi"] = True
                break

    return result


def storage_to_libvirt_helm_values(raw: Any) -> HelmValues:
    """Derive Libvirt Helm values from atmosphere_storage."""

    storage = _parse(raw)
    volumes = storage.volumes
    ephemeral = storage.ephemeral
    default_backend_name = volumes.default if volumes else None
    backends_config = volumes.backends if volumes else {}

    ceph_conf: dict[str, Any] = {"enabled": False}

    if isinstance(ephemeral, EphemeralBackendRbd):
        ceph_conf["enabled"] = True

    for name, backend in backends_config.items():
        if not isinstance(backend, LibvirtSecretSpec):
            continue
        ceph_conf["enabled"] = True
        if name == default_backend_name:
            ceph_conf["cinder"] = {
                "user": backend.ceph_user,
                "secret_uuid": str(backend.secret_uuid),
            }
        else:
            ceph_conf.setdefault("additional_users", []).append(
                {
                    "user": backend.ceph_user,
                    "secret_uuid": str(backend.secret_uuid),
                    "secret_name": f"cinder-volume-rbd-keyring-{name}",
                }
            )

    return {"conf": {"ceph": ceph_conf}}


def storage_to_ceph_provisioners_helm_values(raw: Any) -> HelmValues:
    """Derive Ceph Provisioners Helm values from atmosphere_storage."""

    storage = _parse(raw)
    volumes = storage.volumes
    backends_config = volumes.backends if volumes else {}

    client_conf: dict[str, Any] = {}
    for _name, backend in backends_config.items():
        if isinstance(backend, VolumeBackendRbdEc):
            data_pool = (
                backend.data_pool
                if backend.data_pool
                else f"{backend.pool}.data"
            )
            client_key = f"client.{backend.ceph_user}"
            client_conf[client_key] = {
                "rbd default data pool": data_pool,
            }

    result: HelmValues = {}
    if client_conf:
        result["conf"] = {"ceph": client_conf}

    return result


class FilterModule(object):
    def filters(self) -> dict[str, Any]:
        return {
            "storage_to_cinder_helm_values": storage_to_cinder_helm_values,
            "storage_to_glance_helm_values": storage_to_glance_helm_values,
            "storage_to_nova_helm_values": storage_to_nova_helm_values,
            "storage_to_libvirt_helm_values": storage_to_libvirt_helm_values,
            "storage_to_ceph_provisioners_helm_values": storage_to_ceph_provisioners_helm_values,
        }
