# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from typing_extensions import Self
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

HelmValues = dict[str, Any]


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RbdPoolSpec(_StrictBase):
    pool: str = Field(description="Ceph RBD pool name.")
    crush_rule: str = Field(
        default="replicated_rule",
        description="CRUSH rule applied to the pool.",
    )
    user: str = Field(description="Ceph client user name.")
    chunk_size: int = Field(default=8, description="RBD stripe unit size in MiB.")


class ReplicatedRbdPoolSpec(RbdPoolSpec):
    replication: int = Field(default=3, description="Number of replicas for the pool.")


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
            raise ValueError(f"m ({self.m}) must be less than k ({self.k})")
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


class ImageBackendRbd(ReplicatedRbdPoolSpec):
    type: Literal["rbd"]

    def glance_backend_config(
        self, include_pool_settings: bool = False
    ) -> dict[str, Any]:
        """Generate per-backend Glance config section."""
        config: dict[str, Any] = {
            "rbd_store_pool": self.pool,
            "rbd_store_user": self.user,
            "rbd_store_ceph_conf": "/etc/ceph/ceph.conf",
            "rbd_store_chunk_size": self.chunk_size,
        }
        if include_pool_settings:
            config["rbd_store_replication"] = self.replication
            config["rbd_store_crush_rule"] = self.crush_rule
        return config

    def amend_glance(self, result: HelmValues, name: str, multi_backend: bool) -> None:
        """Amend Glance Helm values for an RBD image backend."""
        result["storage"] = "rbd"
        glance = result["conf"]["glance"]
        if multi_backend:
            glance[name] = self.glance_backend_config()
        else:
            glance["glance_store"] = self.glance_backend_config(
                include_pool_settings=True
            )


class ImageBackendCinder(_StrictBase):
    type: Literal["cinder"]

    def glance_backend_config(
        self, include_pool_settings: bool = False
    ) -> dict[str, Any]:
        """Generate per-backend Glance config section."""
        return {"cinder_catalog_info": "volumev3::internalURL"}

    def amend_glance(self, result: HelmValues, name: str, multi_backend: bool) -> None:
        """Amend Glance Helm values for a Cinder image backend."""
        if multi_backend:
            result["conf"]["glance"][name] = self.glance_backend_config()
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


ImageBackend = Annotated[
    Union[ImageBackendRbd, ImageBackendCinder],
    Field(discriminator="type"),
]


class _HostAttachedVolumeBackend(_StrictBase):
    """Base for volume backends where volumes are attached directly to the host.

    Provides common Cinder amendments (iSCSI enablement, trimmed dependency
    graph) shared by all non-Ceph volume backends.
    """

    _NON_CEPH_INIT_JOBS: list[str] = [
        "cinder-db-sync",
        "cinder-ks-user",
        "cinder-ks-endpoints",
        "cinder-rabbit-init",
    ]

    def amend_cinder(self, result: HelmValues, name: str) -> None:
        """Apply common non-Ceph Cinder amendments."""
        result.setdefault("storage", self.type)
        result["conf"]["enable_iscsi"] = True
        result["dependencies"] = {
            "static": {
                svc: {"jobs": list(self._NON_CEPH_INIT_JOBS)}
                for svc in ("api", "scheduler", "volume", "volume_usage_audit")
            }
        }


class VolumeBackendRbd(ReplicatedRbdPoolSpec, LibvirtSecretSpec):
    """Ceph RBD replicated volume backend."""

    type: Literal["rbd"]

    def cinder_backend_config(self, name: str) -> dict[str, Any]:
        """Generate Cinder backend config for a Ceph RBD replicated backend."""
        return {
            "volume_driver": "cinder.volume.drivers.rbd.RBDDriver",
            "volume_backend_name": name,
            "rbd_pool": self.pool,
            "rbd_ceph_conf": "/etc/ceph/ceph.conf",
            "rbd_flatten_volume_from_snapshot": False,
            "report_discard_supported": True,
            "rbd_max_clone_depth": 5,
            "rbd_store_chunk_size": self.chunk_size,
            "rados_connect_timeout": -1,
            "rbd_user": self.user,
            "rbd_secret_uuid": str(self.secret_uuid),
            "image_volume_cache_enabled": True,
            "image_volume_cache_max_size_gb": 200,
            "image_volume_cache_max_count": 50,
        }

    def amend_cinder(self, result: HelmValues, name: str) -> None:
        """Amend Cinder Helm values for an RBD volume backend."""
        result["storage"] = "ceph"
        result["conf"]["backends"][name] = self.cinder_backend_config(name)
        pools = result["conf"].setdefault("ceph", {}).setdefault("pools", {})
        pools[self.pool] = {
            "replication": self.replication,
            "crush_rule": self.crush_rule,
            "chunk_size": self.chunk_size,
            "app_name": "cinder-volume",
        }


class VolumeBackendRbdEc(ErasureCodedRbdPoolSpec, LibvirtSecretSpec):
    """Ceph RBD erasure-coded volume backend."""

    type: Literal["rbd-ec"]

    def cinder_backend_config(self, name: str) -> dict[str, Any]:
        """Generate Cinder backend config for a Ceph RBD erasure-coded backend."""
        return {
            "volume_driver": "cinder.volume.drivers.rbd.RBDDriver",
            "volume_backend_name": name,
            "rbd_pool": self.pool,
            "rbd_ceph_conf": "/etc/ceph/ceph.conf",
            "rbd_flatten_volume_from_snapshot": False,
            "report_discard_supported": True,
            "rbd_max_clone_depth": 5,
            "rbd_store_chunk_size": self.chunk_size,
            "rados_connect_timeout": -1,
            "rbd_user": self.user,
            "rbd_secret_uuid": str(self.secret_uuid),
            "image_volume_cache_enabled": True,
            "image_volume_cache_max_size_gb": 200,
            "image_volume_cache_max_count": 50,
            "rbd_data_pool": (
                self.data_pool if self.data_pool else f"{self.pool}.data"
            ),
        }

    def amend_cinder(self, result: HelmValues, name: str) -> None:
        """Amend Cinder Helm values for an RBD-EC volume backend."""
        result["storage"] = "ceph"
        result["conf"]["backends"][name] = self.cinder_backend_config(name)
        pools = result["conf"].setdefault("ceph", {}).setdefault("pools", {})
        ec = self.erasure_coded
        pool_config: dict[str, Any] = {
            "app_name": "cinder-volume",
            "erasure_coded": {
                "k": ec.k,
                "m": ec.m,
                "failure_domain": ec.failure_domain,
            },
            "metadata": {
                "replication": self.metadata_replication,
            },
        }
        if ec.device_class is not None:
            pool_config["erasure_coded"]["device_class"] = ec.device_class
        if self.data_pool is not None:
            pool_config["erasure_coded"]["data_pool_name"] = self.data_pool
        pools[self.pool] = pool_config


class VolumeBackendPowerstore(_HostAttachedVolumeBackend):
    """Dell PowerStore volume backend."""

    type: Literal["powerstore"]
    address: str = Field(description="Management address (IP or hostname).")
    username: str = Field(description="Username credential.")
    password: str = Field(description="Password credential.")
    protocol: Literal["fc", "iscsi"] = Field(description="Transport protocol.")

    def cinder_backend_config(self, name: str) -> dict[str, Any]:
        """Generate Cinder backend config for PowerStore."""
        protocol_map = {"fc": "FC", "iscsi": "iSCSI"}
        return {
            "volume_backend_name": name,
            "volume_driver": "cinder.volume.drivers.dell_emc.powerstore.driver.PowerStoreDriver",
            "san_ip": self.address,
            "san_login": self.username,
            "san_password": self.password,
            "storage_protocol": protocol_map[self.protocol],
        }

    def amend_cinder(self, result: HelmValues, name: str) -> None:
        """Amend Cinder Helm values for a PowerStore volume backend."""
        super().amend_cinder(result, name)
        result["conf"]["backends"][name] = self.cinder_backend_config(name)


class _VolumeBackendPureBase(_HostAttachedVolumeBackend):
    """Pure Storage FlashArray volume backend."""

    type: Literal["pure"]
    address: str = Field(description="Management address (IP or hostname).")
    api_token: str = Field(description="API token.")

    @property
    def cinder_driver(self) -> str:
        raise NotImplementedError

    def cinder_backend_config(self, name: str) -> dict[str, Any]:
        """Generate Cinder backend config for Pure Storage."""
        return {
            "volume_backend_name": name,
            "volume_driver": self.cinder_driver,
            "san_ip": self.address,
            "pure_api_token": self.api_token,
            "use_multipath_for_image_xfer": True,
            "pure_eradicate_on_delete": True,
        }

    def amend_cinder(self, result: HelmValues, name: str) -> None:
        """Amend Cinder Helm values for a Pure Storage volume backend."""
        super().amend_cinder(result, name)
        result["conf"]["backends"][name] = self.cinder_backend_config(name)
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
            "cinder_backup": {"container": {"cinder_backup": {"privileged": True}}},
        }


class VolumeBackendPureISCSI(_VolumeBackendPureBase):
    protocol: Literal["iscsi"]

    @property
    def cinder_driver(self) -> str:
        return "cinder.volume.drivers.pure.PureISCSIDriver"


class VolumeBackendPureFC(_VolumeBackendPureBase):
    protocol: Literal["fc"]

    @property
    def cinder_driver(self) -> str:
        return "cinder.volume.drivers.pure.PureFCDriver"


class VolumeBackendPureNVMe(_VolumeBackendPureBase):
    protocol: Literal["nvme"]
    transport: Literal["roce", "tcp"] | None = Field(
        default=None, description="NVMe transport type."
    )

    @property
    def cinder_driver(self) -> str:
        return "cinder.volume.drivers.pure.PureNVMEDriver"

    def cinder_backend_config(self, name: str) -> dict[str, Any]:
        """Generate Cinder backend config for Pure Storage NVMe."""
        config = super().cinder_backend_config(name)
        if self.transport is not None:
            config["pure_nvme_transport"] = self.transport
        return config


VolumeBackendPure = Annotated[
    Union[VolumeBackendPureISCSI, VolumeBackendPureFC, VolumeBackendPureNVMe],
    Field(discriminator="protocol"),
]


class VolumeBackendStorpool(_HostAttachedVolumeBackend):
    """StorPool distributed storage volume backend."""

    type: Literal["storpool"]
    template: str = Field(description="Volume template name.")

    def cinder_backend_config(self, name: str) -> dict[str, Any]:
        """Generate Cinder backend config for StorPool."""
        return {
            "volume_backend_name": name,
            "volume_driver": "cinder.volume.drivers.storpool.StorPoolDriver",
            "storpool_template": self.template,
            "report_discard_supported": True,
        }

    def amend_cinder(self, result: HelmValues, name: str) -> None:
        """Amend Cinder Helm values for a StorPool volume backend."""
        super().amend_cinder(result, name)
        result["conf"]["backends"][name] = self.cinder_backend_config(name)
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


class BackupBackendRbd(ReplicatedRbdPoolSpec):
    type: Literal["rbd"]

    def amend_cinder_backup(self, result: HelmValues) -> None:
        """Amend Cinder Helm values with RBD backup configuration."""
        result["conf"]["cinder"]["DEFAULT"][
            "backup_driver"
        ] = "cinder.backup.drivers.ceph.CephBackupDriver"
        result["conf"]["cinder"]["DEFAULT"]["backup_ceph_conf"] = "/etc/ceph/ceph.conf"
        result["conf"]["cinder"]["DEFAULT"]["backup_ceph_user"] = self.user
        result["conf"]["cinder"]["DEFAULT"]["backup_ceph_pool"] = self.pool

        pools = result["conf"].setdefault("ceph", {}).setdefault("pools", {})
        pools["backup"] = {
            "replication": self.replication,
            "crush_rule": self.crush_rule,
            "chunk_size": self.chunk_size,
            "app_name": "cinder-backup",
        }


class BackupBackendNone(_StrictBase):
    type: Literal["none"]

    def amend_cinder_backup(self, result: HelmValues) -> None:
        """Amend Cinder Helm values to disable backups."""
        result.setdefault("manifests", {})
        result["manifests"]["deployment_backup"] = False
        result["manifests"]["job_backup_storage_init"] = False


BackupBackend = Annotated[
    Union[BackupBackendRbd, BackupBackendNone],
    Field(discriminator="type"),
]


class EphemeralBackendRbd(ReplicatedRbdPoolSpec, LibvirtSecretSpec):
    type: Literal["rbd"]


class EphemeralBackendLocal(_StrictBase):
    type: Literal["local"]


EphemeralBackend = Annotated[
    Union[EphemeralBackendRbd, EphemeralBackendLocal],
    Field(discriminator="type"),
]


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
              user: glance
        volumes:
          default: rbd1
          backends:
            rbd1:
              type: rbd
              pool: cinder.volumes
              user: cinder
              secret_uuid: 457eb676-33da-42ec-9a8c-9293d545c337
        backup:
          type: rbd
          pool: cinder.backups
          user: cinderbackup
        ephemeral:
          type: rbd
          pool: vms
          user: cinder
          secret_uuid: 457eb676-33da-42ec-9a8c-9293d545c337
    """

    images: ImageStorageConfig | None = Field(
        default=None, description="Image configuration (Glance)."
    )
    volumes: VolumeStorageConfig | None = Field(
        default=None, description="Volume configuration (Cinder)."
    )
    backup: BackupBackend | None = Field(
        default=None, description="Backup configuration (Cinder)."
    )
    ephemeral: EphemeralBackend | None = Field(
        default=None, description="Ephemeral disk configuration (Nova)."
    )


def _parse(raw: Any) -> StorageConfig:
    """Validate and parse raw Ansible input into a StorageConfig."""
    return StorageConfig.model_validate(raw)


def storage_to_cinder_helm_values(raw: Any) -> HelmValues:
    """Derive Cinder Helm values from atmosphere_storage."""

    storage = _parse(raw)
    volumes = storage.volumes
    backup = storage.backup
    default_backend = volumes.default if volumes else None
    backends_config = volumes.backends if volumes else {}

    result: HelmValues = {"conf": {"backends": {}, "cinder": {"DEFAULT": {}}}}

    for name, backend in backends_config.items():
        backend.amend_cinder(result, name)

    result["conf"]["cinder"]["DEFAULT"]["enabled_backends"] = ",".join(
        backends_config.keys()
    )
    result["conf"]["cinder"]["DEFAULT"]["default_volume_type"] = default_backend

    if backup is not None:
        backup.amend_cinder_backup(result)

    if result["conf"].get("enable_iscsi") and result.get("storage") != "ceph":
        result.setdefault("manifests", {})
        result["manifests"]["job_storage_init"] = False

    return result


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
            enabled_parts.append(f"{name}:{backend.type}")

        result["conf"]["glance"]["DEFAULT"] = {
            "enabled_backends": ",".join(enabled_parts),
        }
        result["conf"]["glance"]["glance_store"] = {
            "default_backend": default_backend,
        }

    for name, backend in backends_config.items():
        backend.amend_glance(result, name, multi_backend)

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
                    "rbd_user": ephemeral.user,
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

    volumes = storage.volumes
    if volumes:
        for backend in volumes.backends.values():
            if isinstance(backend, _HostAttachedVolumeBackend):
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
                "user": backend.user,
                "secret_uuid": str(backend.secret_uuid),
            }
        else:
            ceph_conf.setdefault("additional_users", []).append(
                {
                    "user": backend.user,
                    "secret_uuid": str(backend.secret_uuid),
                    "secret_name": f"cinder-volume-rbd-keyring-{name.replace('_', '-')}",
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
                backend.data_pool if backend.data_pool else f"{backend.pool}.data"
            )
            client_key = f"client.{backend.user}"
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
