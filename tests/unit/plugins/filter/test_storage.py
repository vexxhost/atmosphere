# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import pytest
from ansible_collections.vexxhost.atmosphere.plugins.filter.storage import (
    FilterModule,
    StorageConfig,
    storage_to_ceph_provisioners_helm_values,
    storage_to_cinder_helm_values,
    storage_to_glance_helm_values,
    storage_to_libvirt_helm_values,
    storage_to_nova_helm_values,
)
from pydantic import ValidationError

DEFAULT_STORAGE = {
    "images": {
        "default": "rbd1",
        "backends": {
            "rbd1": {
                "type": "rbd",
                "pool": "glance.images",
                "replication": 3,
                "crush_rule": "replicated_rule",
                "chunk_size": 8,
                "user": "glance",
            }
        },
    },
    "volumes": {
        "default": "rbd1",
        "backends": {
            "rbd1": {
                "type": "rbd",
                "pool": "cinder.volumes",
                "replication": 3,
                "crush_rule": "replicated_rule",
                "user": "cinder",
                "secret_uuid": "457eb676-33da-42ec-9a8c-9293d545c337",
            }
        },
    },
    "backup": {
        "type": "rbd",
        "pool": "cinder.backups",
        "replication": 3,
        "crush_rule": "replicated_rule",
        "user": "cinderbackup",
    },
    "ephemeral": {
        "type": "rbd",
        "pool": "vms",
        "replication": 3,
        "crush_rule": "replicated_rule",
        "user": "cinder",
        "secret_uuid": "457eb676-33da-42ec-9a8c-9293d545c337",
    },
}

_EC_BACKEND = {
    "type": "rbd-ec",
    "pool": "cinder.volumes.ec",
    "erasure_coded": {
        "k": 4,
        "m": 2,
        "failure_domain": "host",
    },
    "metadata_replication": 3,
    "user": "cinder-ec",
    "secret_uuid": "808c5658-7c46-4818-8f26-82a217e3a57a",
}

_POWERSTORE_BACKEND = {
    "type": "powerstore",
    "address": "10.0.0.1",
    "username": "admin",
    "password": "secret",
    "protocol": "iscsi",
}

_PURE_ISCSI_BACKEND = {
    "type": "pure",
    "protocol": "iscsi",
    "address": "10.0.0.2",
    "api_token": "token123",
}

_STORPOOL_BACKEND = {
    "type": "storpool",
    "template": "hybrid-2ssd",
}

_VAST_BACKEND_WITH_TOKEN = {
    "type": "vast",
    "address": "10.0.0.5",
    "api_token": "vast-api-token",
    "subsystem": "openstack-subsystem",
    "vippool_name": "openstack-vips",
}

_VAST_BACKEND_WITH_USERPASS = {
    "type": "vast",
    "address": "10.0.0.5",
    "username": "admin",
    "password": "secret",
    "subsystem": "openstack-subsystem",
    "vippool_name": "openstack-vips",
}


class TestValidation:
    def test_empty_storage_is_valid(self):
        cfg = StorageConfig.model_validate({})
        assert cfg.images is None
        assert cfg.volumes is None
        assert cfg.backup is None
        assert cfg.ephemeral is None

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            StorageConfig.model_validate({"unknown_field": "value"})

    def test_extra_field_in_volume_backend_rejected(self):
        with pytest.raises(ValidationError):
            StorageConfig.model_validate(
                {
                    "volumes": {
                        "default": "rbd1",
                        "backends": {
                            "rbd1": {
                                **DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                                "extra": True,
                            }
                        },
                    }
                }
            )

    def test_erasure_coded_m_ge_k_rejected(self):
        with pytest.raises(ValidationError, match="m.*must be less than k"):
            StorageConfig.model_validate(
                {
                    "volumes": {
                        "default": "ec1",
                        "backends": {
                            "ec1": {
                                "type": "rbd-ec",
                                "pool": "test",
                                "erasure_coded": {
                                    "k": 2,
                                    "m": 3,
                                    "failure_domain": "host",
                                },
                                "metadata_replication": 3,
                                "user": "cinder",
                                "secret_uuid": "457eb676-33da-42ec-9a8c-9293d545c337",
                            }
                        },
                    }
                }
            )

    def test_erasure_coded_m_equal_k_rejected(self):
        with pytest.raises(ValidationError, match="m.*must be less than k"):
            StorageConfig.model_validate(
                {
                    "volumes": {
                        "default": "ec1",
                        "backends": {
                            "ec1": {
                                "type": "rbd-ec",
                                "pool": "test",
                                "erasure_coded": {
                                    "k": 3,
                                    "m": 3,
                                    "failure_domain": "host",
                                },
                                "metadata_replication": 3,
                                "user": "cinder",
                                "secret_uuid": "457eb676-33da-42ec-9a8c-9293d545c337",
                            }
                        },
                    }
                }
            )

    def test_image_default_not_in_backends(self):
        with pytest.raises(ValidationError, match="default.*not in backends"):
            StorageConfig.model_validate(
                {
                    "images": {
                        "default": "missing",
                        "backends": {
                            "rbd1": {
                                "type": "rbd",
                                "pool": "glance.images",
                                "user": "glance",
                            },
                        },
                    }
                }
            )

    def test_volume_default_not_in_backends(self):
        with pytest.raises(ValidationError, match="default.*not in backends"):
            StorageConfig.model_validate(
                {
                    "volumes": {
                        "default": "missing",
                        "backends": {
                            "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                        },
                    }
                }
            )

    def test_empty_backends_rejected(self):
        with pytest.raises(ValidationError):
            StorageConfig.model_validate(
                {
                    "volumes": {
                        "default": "rbd1",
                        "backends": {},
                    }
                }
            )

    def test_invalid_backend_type_rejected(self):
        with pytest.raises(ValidationError):
            StorageConfig.model_validate(
                {
                    "volumes": {
                        "default": "bad",
                        "backends": {
                            "bad": {"type": "nonexistent"},
                        },
                    }
                }
            )

    def test_invalid_secret_uuid_rejected(self):
        with pytest.raises(ValidationError):
            StorageConfig.model_validate(
                {
                    "volumes": {
                        "default": "rbd1",
                        "backends": {
                            "rbd1": {
                                **DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                                "secret_uuid": "not-a-uuid",
                            }
                        },
                    }
                }
            )

    def test_erasure_coded_k_below_minimum_rejected(self):
        with pytest.raises(ValidationError):
            StorageConfig.model_validate(
                {
                    "volumes": {
                        "default": "ec1",
                        "backends": {
                            "ec1": {
                                "type": "rbd-ec",
                                "pool": "test",
                                "erasure_coded": {
                                    "k": 1,
                                    "m": 1,
                                    "failure_domain": "host",
                                },
                                "metadata_replication": 3,
                                "user": "cinder",
                                "secret_uuid": "457eb676-33da-42ec-9a8c-9293d545c337",
                            }
                        },
                    }
                }
            )

    def test_defaults_applied(self):
        """Verify optional fields use their defaults when omitted."""
        cfg = StorageConfig.model_validate(
            {
                "volumes": {
                    "default": "rbd1",
                    "backends": {
                        "rbd1": {
                            "type": "rbd",
                            "pool": "test",
                            "user": "cinder",
                            "secret_uuid": "457eb676-33da-42ec-9a8c-9293d545c337",
                        }
                    },
                }
            }
        )
        backend = cfg.volumes.backends["rbd1"]
        assert backend.replication == 3
        assert backend.crush_rule == "replicated_rule"
        assert backend.chunk_size == 8


class TestStorageToCinderHelmValues:
    def test_default_rbd(self):
        result = storage_to_cinder_helm_values(DEFAULT_STORAGE)
        assert result["storage"] == "ceph"
        assert "rbd1" in result["conf"]["backends"]
        backend = result["conf"]["backends"]["rbd1"]
        assert backend["volume_driver"] == "cinder.volume.drivers.rbd.RBDDriver"
        assert backend["rbd_pool"] == "cinder.volumes"
        assert backend["rbd_user"] == "cinder"
        assert backend["rbd_secret_uuid"] == "457eb676-33da-42ec-9a8c-9293d545c337"
        assert backend["rbd_ceph_conf"] == "/etc/ceph/ceph.conf"
        assert backend["rbd_flatten_volume_from_snapshot"] is False
        assert backend["report_discard_supported"] is True
        assert backend["rbd_max_clone_depth"] == 5
        assert backend["rbd_store_chunk_size"] == 8
        assert backend["rados_connect_timeout"] == -1
        assert backend["image_volume_cache_enabled"] is True
        assert backend["image_volume_cache_max_size_gb"] == 200
        assert backend["image_volume_cache_max_count"] == 50
        assert result["conf"]["cinder"]["DEFAULT"]["enabled_backends"] == "rbd1"
        assert result["conf"]["cinder"]["DEFAULT"]["default_volume_type"] == "rbd1"

    def test_rbd_custom_chunk_size(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": {
                        **DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                        "chunk_size": 16,
                    }
                },
            },
        }
        result = storage_to_cinder_helm_values(storage)
        assert result["conf"]["backends"]["rbd1"]["rbd_store_chunk_size"] == 16
        assert result["conf"]["ceph"]["pools"]["cinder.volumes"]["chunk_size"] == 16

    def test_multiple_rbd_backends(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "rbd2": {
                        "type": "rbd",
                        "pool": "cinder.volumes.ssd",
                        "replication": 2,
                        "crush_rule": "ssd_rule",
                        "user": "cinder-ssd",
                        "secret_uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    },
                },
            },
        }
        result = storage_to_cinder_helm_values(storage)
        assert "rbd1" in result["conf"]["backends"]
        assert "rbd2" in result["conf"]["backends"]
        assert result["conf"]["backends"]["rbd2"]["rbd_pool"] == "cinder.volumes.ssd"
        assert result["conf"]["backends"]["rbd2"]["rbd_user"] == "cinder-ssd"
        pools = result["conf"]["ceph"]["pools"]
        assert "cinder.volumes" in pools
        assert "cinder.volumes.ssd" in pools
        assert pools["cinder.volumes.ssd"]["replication"] == 2
        assert pools["cinder.volumes.ssd"]["crush_rule"] == "ssd_rule"
        assert "rbd1,rbd2" == result["conf"]["cinder"]["DEFAULT"]["enabled_backends"]

    def test_ceph_backup_config(self):
        result = storage_to_cinder_helm_values(DEFAULT_STORAGE)
        cinder_default = result["conf"]["cinder"]["DEFAULT"]
        assert (
            cinder_default["backup_driver"]
            == "cinder.backup.drivers.ceph.CephBackupDriver"
        )
        assert cinder_default["backup_ceph_conf"] == "/etc/ceph/ceph.conf"
        assert cinder_default["backup_ceph_user"] == "cinderbackup"
        assert cinder_default["backup_ceph_pool"] == "cinder.backups"

    def test_ceph_pools_generated(self):
        result = storage_to_cinder_helm_values(DEFAULT_STORAGE)
        pools = result["conf"]["ceph"]["pools"]
        assert "cinder.volumes" in pools
        assert pools["cinder.volumes"]["replication"] == 3
        assert pools["cinder.volumes"]["crush_rule"] == "replicated_rule"
        assert pools["cinder.volumes"]["chunk_size"] == 8
        assert pools["cinder.volumes"]["app_name"] == "cinder-volume"
        assert "backup" in pools
        assert pools["backup"]["app_name"] == "cinder-backup"

    def test_ec_pool_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "rbd_ec": _EC_BACKEND,
                },
            },
        }
        result = storage_to_cinder_helm_values(storage)

        assert "rbd_ec" in result["conf"]["backends"]
        ec_backend = result["conf"]["backends"]["rbd_ec"]
        assert ec_backend["rbd_pool"] == "cinder.volumes.ec"
        assert ec_backend["rbd_data_pool"] == "cinder.volumes.ec.data"
        assert ec_backend["rbd_user"] == "cinder-ec"
        assert result["conf"]["cinder"]["DEFAULT"]["enabled_backends"] == "rbd1,rbd_ec"

        pools = result["conf"]["ceph"]["pools"]
        assert "cinder.volumes.ec" in pools
        ec_pool = pools["cinder.volumes.ec"]
        assert ec_pool["erasure_coded"]["k"] == 4
        assert ec_pool["erasure_coded"]["m"] == 2
        assert ec_pool["erasure_coded"]["failure_domain"] == "host"
        assert ec_pool["metadata"]["replication"] == 3
        assert ec_pool["app_name"] == "cinder-volume"

    def test_ec_with_device_class(self):
        ec_backend = {
            **_EC_BACKEND,
            "erasure_coded": {**_EC_BACKEND["erasure_coded"], "device_class": "ssd"},
        }
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "ec1",
                "backends": {"ec1": ec_backend},
            },
        }
        result = storage_to_cinder_helm_values(storage)
        pool = result["conf"]["ceph"]["pools"]["cinder.volumes.ec"]
        assert pool["erasure_coded"]["device_class"] == "ssd"

    def test_ec_with_custom_data_pool(self):
        ec_backend = {**_EC_BACKEND, "data_pool": "custom-data-pool"}
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "ec1",
                "backends": {"ec1": ec_backend},
            },
        }
        result = storage_to_cinder_helm_values(storage)
        assert result["conf"]["backends"]["ec1"]["rbd_data_pool"] == "custom-data-pool"
        pool = result["conf"]["ceph"]["pools"]["cinder.volumes.ec"]
        assert pool["erasure_coded"]["data_pool_name"] == "custom-data-pool"

    def test_powerstore_backend_iscsi(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "ps",
                "backends": {"ps": _POWERSTORE_BACKEND},
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)

        backend = result["conf"]["backends"]["ps"]
        assert "PowerStoreDriver" in backend["volume_driver"]
        assert backend["san_ip"] == "10.0.0.1"
        assert backend["san_login"] == "admin"
        assert backend["san_password"] == "secret"
        assert backend["storage_protocol"] == "iSCSI"
        assert result["conf"]["enable_iscsi"] is True
        assert result["manifests"]["job_storage_init"] is False

    def test_powerstore_backend_fc(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "ps",
                "backends": {
                    "ps": {**_POWERSTORE_BACKEND, "protocol": "fc"},
                },
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)
        assert result["conf"]["backends"]["ps"]["storage_protocol"] == "FC"

    def test_pure_iscsi_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "pure",
                "backends": {"pure": _PURE_ISCSI_BACKEND},
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)

        backend = result["conf"]["backends"]["pure"]
        assert backend["volume_driver"] == "cinder.volume.drivers.pure.PureISCSIDriver"
        assert backend["san_ip"] == "10.0.0.2"
        assert backend["pure_api_token"] == "token123"
        assert backend["use_multipath_for_image_xfer"] is True
        assert backend["pure_eradicate_on_delete"] is True
        assert result["conf"]["enable_iscsi"] is True
        sc = result["pod"]["security_context"]
        assert sc["cinder_volume"]["container"]["cinder_volume"]["privileged"] is True
        assert sc["cinder_backup"]["container"]["cinder_backup"]["privileged"] is True
        assert result["pod"]["useHostNetwork"] == {"volume": True, "backup": True}

    def test_pure_fc_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "pure",
                "backends": {
                    "pure": {
                        "type": "pure",
                        "protocol": "fc",
                        "address": "10.0.0.3",
                        "api_token": "fc-token",
                    },
                },
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)
        assert result["conf"]["backends"]["pure"]["volume_driver"] == (
            "cinder.volume.drivers.pure.PureFCDriver"
        )

    def test_pure_nvme_backend_without_transport(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "pure",
                "backends": {
                    "pure": {
                        "type": "pure",
                        "protocol": "nvme",
                        "address": "10.0.0.4",
                        "api_token": "nvme-token",
                    },
                },
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)
        backend = result["conf"]["backends"]["pure"]
        assert backend["volume_driver"] == "cinder.volume.drivers.pure.PureNVMEDriver"
        assert "pure_nvme_transport" not in backend

    def test_pure_nvme_backend_with_transport(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "pure",
                "backends": {
                    "pure": {
                        "type": "pure",
                        "protocol": "nvme",
                        "address": "10.0.0.4",
                        "api_token": "nvme-token",
                        "transport": "roce",
                    },
                },
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)
        assert result["conf"]["backends"]["pure"]["pure_nvme_transport"] == "roce"

    def test_storpool_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "sp",
                "backends": {"sp": _STORPOOL_BACKEND},
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)

        backend = result["conf"]["backends"]["sp"]
        assert (
            backend["volume_driver"] == "cinder.volume.drivers.storpool.StorPoolDriver"
        )
        assert backend["storpool_template"] == "hybrid-2ssd"
        assert backend["report_discard_supported"] is True
        assert result["pod"]["useHostNetwork"] == {"volume": True}
        mounts = result["pod"]["mounts"]["cinder_volume"]
        assert len(mounts["volumeMounts"]) == 2
        assert len(mounts["volumes"]) == 2

    def test_vast_backend_with_api_token(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "vast",
                "backends": {"vast": _VAST_BACKEND_WITH_TOKEN},
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)

        backend = result["conf"]["backends"]["vast"]
        assert (
            backend["volume_driver"]
            == "cinder.volume.drivers.vastdata.driver.VASTVolumeDriver"
        )
        assert backend["san_ip"] == "10.0.0.5"
        assert backend["vast_api_token"] == "vast-api-token"
        assert backend["vast_subsystem"] == "openstack-subsystem"
        assert backend["vast_vippool_name"] == "openstack-vips"
        assert "san_login" not in backend
        assert "san_password" not in backend
        assert "vast_tenant_name" not in backend
        assert result["conf"]["enable_iscsi"] is True

    def test_vast_backend_with_username_password(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "vast",
                "backends": {"vast": _VAST_BACKEND_WITH_USERPASS},
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)

        backend = result["conf"]["backends"]["vast"]
        assert backend["san_login"] == "admin"
        assert backend["san_password"] == "secret"
        assert "vast_api_token" not in backend

    def test_vast_backend_with_tenant_name(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "vast",
                "backends": {
                    "vast": {**_VAST_BACKEND_WITH_TOKEN, "tenant_name": "my-tenant"}
                },
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)
        assert result["conf"]["backends"]["vast"]["vast_tenant_name"] == "my-tenant"

    def test_vast_backend_missing_credentials_raises(self):
        with pytest.raises(Exception):
            StorageConfig.model_validate(
                {
                    **DEFAULT_STORAGE,
                    "volumes": {
                        "default": "vast",
                        "backends": {
                            "vast": {
                                "type": "vast",
                                "address": "10.0.0.5",
                                "subsystem": "openstack-subsystem",
                                "vippool_name": "openstack-vips",
                            }
                        },
                    },
                }
            )

    def test_no_backup(self):
        storage = {
            **DEFAULT_STORAGE,
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)
        assert result["manifests"]["deployment_backup"] is False
        assert result["manifests"]["job_backup_storage_init"] is False

    def test_no_backup_config(self):
        """When backups is omitted entirely, no backup keys are set."""
        storage = {
            "volumes": DEFAULT_STORAGE["volumes"],
        }
        result = storage_to_cinder_helm_values(storage)
        cinder_default = result["conf"]["cinder"]["DEFAULT"]
        assert "backup_driver" not in cinder_default
        assert "manifests" not in result

    def test_no_volumes_config(self):
        """When volumes is omitted, result has empty backends and no default."""
        result = storage_to_cinder_helm_values({})
        assert result["conf"]["backends"] == {}
        assert result["conf"]["cinder"]["DEFAULT"]["enabled_backends"] == ""
        assert result["conf"]["cinder"]["DEFAULT"]["default_volume_type"] is None

    def test_mixed_ceph_and_non_ceph_backends(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "powerstore": _POWERSTORE_BACKEND,
                },
            },
        }
        result = storage_to_cinder_helm_values(storage)

        assert result["storage"] == "ceph"
        assert "rbd1" in result["conf"]["backends"]
        assert "powerstore" in result["conf"]["backends"]
        assert result["conf"]["enable_iscsi"] is True
        assert (
            result["conf"]["cinder"]["DEFAULT"]["enabled_backends"] == "rbd1,powerstore"
        )
        assert "cinder.volumes" in result["conf"]["ceph"]["pools"]
        # storage-init NOT disabled when ceph is present
        assert result.get("manifests", {}).get("job_storage_init") is not False

    def test_non_ceph_volumes_with_ceph_backup(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "powerstore",
                "backends": {"powerstore": _POWERSTORE_BACKEND},
            },
            "backup": DEFAULT_STORAGE["backup"],
        }
        result = storage_to_cinder_helm_values(storage)

        assert "ceph" in result["conf"]
        assert "backup" in result["conf"]["ceph"]["pools"]
        assert result["conf"]["ceph"]["pools"]["backup"]["app_name"] == "cinder-backup"
        assert result["conf"]["cinder"]["DEFAULT"]["backup_driver"] == (
            "cinder.backup.drivers.ceph.CephBackupDriver"
        )

    def test_non_ceph_dependencies_set(self):
        """Non-Ceph backends set trimmed dependency graph."""
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "ps",
                "backends": {"ps": _POWERSTORE_BACKEND},
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)
        deps = result["dependencies"]["static"]
        for svc in ("api", "scheduler", "volume", "volume_usage_audit"):
            assert svc in deps
            assert "cinder-db-sync" in deps[svc]["jobs"]
            assert "cinder-ks-user" in deps[svc]["jobs"]
            assert "cinder-ks-endpoints" in deps[svc]["jobs"]
            assert "cinder-rabbit-init" in deps[svc]["jobs"]

    def test_multiple_non_ceph_backends(self):
        """Multiple non-Ceph backends: storage type from first, iscsi enabled."""
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "ps",
                "backends": {
                    "ps": _POWERSTORE_BACKEND,
                    "pure": _PURE_ISCSI_BACKEND,
                },
            },
            "backup": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)
        # First backend sets storage type
        assert result["storage"] == "powerstore"
        assert result["conf"]["enable_iscsi"] is True
        assert "ps" in result["conf"]["backends"]
        assert "pure" in result["conf"]["backends"]
        assert result["conf"]["cinder"]["DEFAULT"]["enabled_backends"] == "ps,pure"


class TestStorageToGlanceHelmValues:
    def test_single_rbd_backend(self):
        result = storage_to_glance_helm_values(DEFAULT_STORAGE)
        assert result["storage"] == "rbd"
        glance_store = result["conf"]["glance"]["glance_store"]
        assert glance_store["rbd_store_pool"] == "glance.images"
        assert glance_store["rbd_store_user"] == "glance"
        assert glance_store["rbd_store_ceph_conf"] == "/etc/ceph/ceph.conf"
        assert glance_store["rbd_store_chunk_size"] == 8
        # Single-backend includes pool settings
        assert glance_store["rbd_store_replication"] == 3
        assert glance_store["rbd_store_crush_rule"] == "replicated_rule"

    def test_single_rbd_no_enabled_backends_key(self):
        """Single backend mode does not set DEFAULT/enabled_backends."""
        result = storage_to_glance_helm_values(DEFAULT_STORAGE)
        assert "DEFAULT" not in result["conf"]["glance"]

    def test_multi_backend_with_cinder(self):
        storage = {
            **DEFAULT_STORAGE,
            "images": {
                "default": "rbd1",
                "backends": {
                    "rbd1": {
                        "type": "rbd",
                        "pool": "glance.images",
                        "user": "glance",
                    },
                    "cinder_store": {
                        "type": "cinder",
                    },
                },
            },
        }
        result = storage_to_glance_helm_values(storage)

        glance_conf = result["conf"]["glance"]
        assert "rbd1:rbd" in glance_conf["DEFAULT"]["enabled_backends"]
        assert "cinder_store:cinder" in glance_conf["DEFAULT"]["enabled_backends"]
        assert glance_conf["glance_store"]["default_backend"] == "rbd1"
        assert glance_conf["rbd1"]["rbd_store_pool"] == "glance.images"
        # Multi-backend rbd config does NOT include pool settings
        assert "rbd_store_replication" not in glance_conf["rbd1"]
        assert "rbd_store_crush_rule" not in glance_conf["rbd1"]
        assert (
            glance_conf["cinder_store"]["cinder_catalog_info"]
            == "volumev3::internalURL"
        )
        assert (
            result["pod"]["security_context"]["glance"]["container"]["glance_api"][
                "privileged"
            ]
            is True
        )

    def test_multi_backend_rbd_only(self):
        """Multiple RBD backends still use multi-backend mode."""
        storage = {
            **DEFAULT_STORAGE,
            "images": {
                "default": "rbd1",
                "backends": {
                    "rbd1": {
                        "type": "rbd",
                        "pool": "glance.images",
                        "user": "glance",
                    },
                    "rbd2": {
                        "type": "rbd",
                        "pool": "glance.images.ssd",
                        "user": "glance-ssd",
                    },
                },
            },
        }
        result = storage_to_glance_helm_values(storage)
        glance_conf = result["conf"]["glance"]
        assert "rbd1:rbd" in glance_conf["DEFAULT"]["enabled_backends"]
        assert "rbd2:rbd" in glance_conf["DEFAULT"]["enabled_backends"]
        assert glance_conf["glance_store"]["default_backend"] == "rbd1"
        assert glance_conf["rbd1"]["rbd_store_pool"] == "glance.images"
        assert glance_conf["rbd2"]["rbd_store_pool"] == "glance.images.ssd"

    def test_single_cinder_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "images": {
                "default": "cinder_store",
                "backends": {
                    "cinder_store": {
                        "type": "cinder",
                    },
                },
            },
        }
        result = storage_to_glance_helm_values(storage)
        # No rbd storage type
        assert "storage" not in result
        assert result["pod"]["useHostNetwork"] == {"api": True}
        # Single-backend cinder: no glance_store config set (no rbd pool)
        assert "glance_store" not in result.get("conf", {}).get("glance", {})

    def test_no_images_config(self):
        """When images is omitted, conf key is removed."""
        result = storage_to_glance_helm_values({})
        assert "conf" not in result


class TestStorageToNovaHelmValues:
    def test_rbd_ephemeral(self):
        result = storage_to_nova_helm_values(DEFAULT_STORAGE)
        assert result["conf"]["ceph"]["enabled"] is True
        libvirt = result["conf"]["nova"]["libvirt"]
        assert libvirt["images_type"] == "rbd"
        assert libvirt["images_rbd_pool"] == "vms"
        assert libvirt["images_rbd_ceph_conf"] == "/etc/ceph/ceph.conf"
        assert libvirt["rbd_user"] == "cinder"
        assert libvirt["rbd_secret_uuid"] == "457eb676-33da-42ec-9a8c-9293d545c337"
        assert result["manifests"]["job_storage_init"] is True
        assert result["rbd_pool"]["app_name"] == "nova-vms"
        assert result["rbd_pool"]["replication"] == 3
        assert result["rbd_pool"]["crush_rule"] == "replicated_rule"
        assert result["rbd_pool"]["chunk_size"] == 8

    def test_local_ephemeral(self):
        storage = {
            **DEFAULT_STORAGE,
            "ephemeral": {"type": "local"},
        }
        result = storage_to_nova_helm_values(storage)
        assert result["conf"]["ceph"]["enabled"] is True
        assert result["conf"]["nova"]["libvirt"]["images_type"] == "qcow2"
        assert "manifests" not in result
        assert "rbd_pool" not in result

    def test_no_ephemeral_config(self):
        """When ephemeral is omitted and volumes are all Ceph, no conf set."""
        result = storage_to_nova_helm_values(
            {
                "volumes": DEFAULT_STORAGE["volumes"],
            }
        )
        assert "ceph" not in result.get("conf", {})
        assert "nova" not in result.get("conf", {})

    def test_no_ephemeral_no_volumes(self):
        """Completely empty storage produces empty result."""
        result = storage_to_nova_helm_values({})
        assert result == {}

    def test_iscsi_from_volume_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "ps",
                "backends": {"ps": _POWERSTORE_BACKEND},
            },
        }
        result = storage_to_nova_helm_values(storage)
        assert result["conf"]["enable_iscsi"] is True

    def test_rbd_volumes_no_iscsi(self):
        """RBD-only volumes do not set enable_iscsi."""
        result = storage_to_nova_helm_values(DEFAULT_STORAGE)
        assert result["conf"].get("enable_iscsi") is None

    def test_mixed_ceph_ephemeral_and_non_ceph_volumes(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "powerstore": _POWERSTORE_BACKEND,
                },
            },
        }
        result = storage_to_nova_helm_values(storage)
        assert result["conf"]["ceph"]["enabled"] is True
        assert result["conf"]["nova"]["libvirt"]["images_type"] == "rbd"
        assert result["conf"]["enable_iscsi"] is True

    def test_local_ephemeral_with_non_ceph_volumes(self):
        """Local ephemeral + non-Ceph volumes: ceph disabled, iscsi enabled."""
        storage = {
            "ephemeral": {"type": "local"},
            "volumes": {
                "default": "ps",
                "backends": {"ps": _POWERSTORE_BACKEND},
            },
        }
        result = storage_to_nova_helm_values(storage)
        assert result["conf"]["ceph"]["enabled"] is False
        assert result["conf"]["nova"]["libvirt"]["images_type"] == "qcow2"
        assert result["conf"]["enable_iscsi"] is True


class TestStorageToLibvirtHelmValues:
    def test_default_ceph(self):
        result = storage_to_libvirt_helm_values(DEFAULT_STORAGE)
        assert result["conf"]["ceph"]["enabled"] is True
        assert result["conf"]["ceph"]["cinder"]["user"] == "cinder"
        assert (
            result["conf"]["ceph"]["cinder"]["secret_uuid"]
            == "457eb676-33da-42ec-9a8c-9293d545c337"
        )

    def test_additional_users_for_ec_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "rbd_ec": _EC_BACKEND,
                },
            },
        }
        result = storage_to_libvirt_helm_values(storage)
        additional = result["conf"]["ceph"]["additional_users"]
        assert len(additional) == 1
        assert additional[0]["user"] == "cinder-ec"
        assert additional[0]["secret_uuid"] == "808c5658-7c46-4818-8f26-82a217e3a57a"
        assert additional[0]["secret_name"] == "cinder-volume-rbd-keyring-rbd-ec"

    def test_multiple_additional_users(self):
        """Multiple non-default RBD backends produce multiple additional_users."""
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "rbd2": {
                        "type": "rbd",
                        "pool": "cinder.ssd",
                        "user": "cinder-ssd",
                        "secret_uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    },
                    "rbd3": {
                        "type": "rbd",
                        "pool": "cinder.nvme",
                        "user": "cinder-nvme",
                        "secret_uuid": "11111111-2222-3333-4444-555555555555",
                    },
                },
            },
        }
        result = storage_to_libvirt_helm_values(storage)
        assert result["conf"]["ceph"]["cinder"]["user"] == "cinder"
        additional = result["conf"]["ceph"]["additional_users"]
        assert len(additional) == 2
        users = {u["user"] for u in additional}
        assert users == {"cinder-ssd", "cinder-nvme"}

    def test_no_ceph(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "ps",
                "backends": {"ps": _POWERSTORE_BACKEND},
            },
            "ephemeral": {"type": "local"},
        }
        result = storage_to_libvirt_helm_values(storage)
        assert result["conf"]["ceph"]["enabled"] is False
        assert "cinder" not in result["conf"]["ceph"]
        assert "additional_users" not in result["conf"]["ceph"]

    def test_mixed_ceph_and_non_ceph_volumes(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "powerstore": _POWERSTORE_BACKEND,
                },
            },
        }
        result = storage_to_libvirt_helm_values(storage)
        assert result["conf"]["ceph"]["enabled"] is True
        assert result["conf"]["ceph"]["cinder"]["user"] == "cinder"
        # Non-ceph backend does not produce additional_users
        assert "additional_users" not in result["conf"]["ceph"]

    def test_ephemeral_rbd_only_no_volumes(self):
        """Ephemeral RBD with no volumes: ceph enabled but no cinder key."""
        storage = {
            "ephemeral": DEFAULT_STORAGE["ephemeral"],
        }
        result = storage_to_libvirt_helm_values(storage)
        assert result["conf"]["ceph"]["enabled"] is True
        assert "cinder" not in result["conf"]["ceph"]

    def test_no_volumes_no_ephemeral(self):
        """Completely empty: ceph disabled."""
        result = storage_to_libvirt_helm_values({})
        assert result["conf"]["ceph"]["enabled"] is False

    def test_ephemeral_rbd_with_non_ceph_volumes(self):
        """Ephemeral RBD + non-Ceph volumes: ceph enabled from ephemeral."""
        storage = {
            "ephemeral": DEFAULT_STORAGE["ephemeral"],
            "volumes": {
                "default": "ps",
                "backends": {"ps": _POWERSTORE_BACKEND},
            },
        }
        result = storage_to_libvirt_helm_values(storage)
        assert result["conf"]["ceph"]["enabled"] is True
        # No cinder key because no ceph volume backends
        assert "cinder" not in result["conf"]["ceph"]


class TestStorageToCephProvisionersHelmValues:
    def test_no_ec_backends(self):
        result = storage_to_ceph_provisioners_helm_values(DEFAULT_STORAGE)
        assert result == {}

    def test_no_volumes_config(self):
        result = storage_to_ceph_provisioners_helm_values({})
        assert result == {}

    def test_ec_backend_generates_client_conf(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "rbd_ec": _EC_BACKEND,
                },
            },
        }
        result = storage_to_ceph_provisioners_helm_values(storage)
        client = result["conf"]["ceph"]["client.cinder-ec"]
        assert client["rbd default data pool"] == "cinder.volumes.ec.data"

    def test_ec_custom_data_pool(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "rbd_ec": {**_EC_BACKEND, "data_pool": "custom-data"},
                },
            },
        }
        result = storage_to_ceph_provisioners_helm_values(storage)
        client = result["conf"]["ceph"]["client.cinder-ec"]
        assert client["rbd default data pool"] == "custom-data"

    def test_multiple_ec_backends(self):
        """Multiple EC backends each generate their own client conf."""
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "ec1",
                "backends": {
                    "ec1": _EC_BACKEND,
                    "ec2": {
                        **_EC_BACKEND,
                        "pool": "cinder.volumes.ec2",
                        "user": "cinder-ec2",
                        "secret_uuid": "11111111-2222-3333-4444-555555555555",
                    },
                },
            },
        }
        result = storage_to_ceph_provisioners_helm_values(storage)
        assert "client.cinder-ec" in result["conf"]["ceph"]
        assert "client.cinder-ec2" in result["conf"]["ceph"]
        assert result["conf"]["ceph"]["client.cinder-ec2"]["rbd default data pool"] == (
            "cinder.volumes.ec2.data"
        )


class TestFilterModule:
    def test_returns_all_filters(self):
        fm = FilterModule()
        filters = fm.filters()
        assert set(filters.keys()) == {
            "storage_to_cinder_helm_values",
            "storage_to_glance_helm_values",
            "storage_to_nova_helm_values",
            "storage_to_libvirt_helm_values",
            "storage_to_ceph_provisioners_helm_values",
        }
        for name, func in filters.items():
            assert callable(func)
