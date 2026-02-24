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

from ansible_collections.vexxhost.atmosphere.plugins.filter.storage import (
    storage_to_ceph_provisioners_helm_values,
    storage_to_cinder_helm_values,
    storage_to_glance_helm_values,
    storage_to_libvirt_helm_values,
    storage_to_nova_helm_values,
)

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
                "ceph_user": "glance",
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
                "ceph_user": "cinder",
                "secret_uuid": "457eb676-33da-42ec-9a8c-9293d545c337",
            }
        },
    },
    "backups": {
        "type": "rbd",
        "pool": "cinder.backups",
        "replication": 3,
        "crush_rule": "replicated_rule",
        "ceph_user": "cinderbackup",
    },
    "ephemeral": {
        "type": "rbd",
        "pool": "vms",
        "replication": 3,
        "crush_rule": "replicated_rule",
        "ceph_user": "cinder",
        "secret_uuid": "457eb676-33da-42ec-9a8c-9293d545c337",
    },
}


class TestStorageToCinderHelmValues:
    def test_default_rbd(self):
        result = storage_to_cinder_helm_values(DEFAULT_STORAGE)
        assert result["storage"] == "ceph"
        assert "rbd1" in result["conf"]["backends"]
        backend = result["conf"]["backends"]["rbd1"]
        assert backend["volume_driver"] == "cinder.volume.drivers.rbd.RBDDriver"
        assert backend["rbd_pool"] == "cinder.volumes"
        assert backend["rbd_user"] == "cinder"
        assert result["conf"]["cinder"]["DEFAULT"]["enabled_backends"] == "rbd1"
        assert result["conf"]["cinder"]["DEFAULT"]["default_volume_type"] == "rbd1"

    def test_ceph_backup_config(self):
        result = storage_to_cinder_helm_values(DEFAULT_STORAGE)
        cinder_default = result["conf"]["cinder"]["DEFAULT"]
        assert cinder_default["backup_driver"] == "cinder.backup.drivers.ceph.CephBackupDriver"
        assert cinder_default["backup_ceph_user"] == "cinderbackup"
        assert cinder_default["backup_ceph_pool"] == "cinder.backups"

    def test_ceph_pools_generated(self):
        result = storage_to_cinder_helm_values(DEFAULT_STORAGE)
        pools = result["conf"]["ceph"]["pools"]
        assert "cinder.volumes" in pools
        assert pools["cinder.volumes"]["replication"] == 3
        assert "backup" in pools

    def test_ec_pool_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "rbd_ec": {
                        "type": "rbd-ec",
                        "pool": "cinder.volumes.ec",
                        "erasure_coded": {
                            "k": 4,
                            "m": 2,
                            "failure_domain": "host",
                        },
                        "metadata_replication": 3,
                        "ceph_user": "cinder-ec",
                        "secret_uuid": "808c5658-7c46-4818-8f26-82a217e3a57a",
                    },
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
        assert pools["cinder.volumes.ec"]["erasure_coded"]["k"] == 4

    def test_powerstore_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "powerstore",
                "backends": {
                    "powerstore": {
                        "type": "powerstore",
                        "ip": "10.0.0.1",
                        "login": "admin",
                        "password": "secret",
                        "protocol": "iscsi",
                    }
                },
            },
            "backups": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)

        backend = result["conf"]["backends"]["powerstore"]
        assert "PowerStoreDriver" in backend["volume_driver"]
        assert backend["san_ip"] == "10.0.0.1"
        assert result["conf"]["enable_iscsi"] is True
        assert result["manifests"]["job_storage_init"] is False
        assert result["manifests"]["deployment_backup"] is False

    def test_pure_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "purestorage",
                "backends": {
                    "purestorage": {
                        "type": "pure",
                        "protocol": "iscsi",
                        "ip": "10.0.0.2",
                        "api_token": "token123",
                    }
                },
            },
            "backups": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)

        backend = result["conf"]["backends"]["purestorage"]
        assert backend["volume_driver"] == "cinder.volume.drivers.pure.PureISCSIDriver"
        assert result["conf"]["enable_iscsi"] is True
        assert result["pod"]["security_context"]["cinder_volume"]["container"]["cinder_volume"]["privileged"] is True

    def test_storpool_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "storpool",
                "backends": {
                    "storpool": {
                        "type": "storpool",
                        "template": "hybrid-2ssd",
                    }
                },
            },
            "backups": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)

        backend = result["conf"]["backends"]["storpool"]
        assert "StorPoolDriver" in backend["volume_driver"]
        assert result["pod"]["useHostNetwork"] == {"volume": True}
        assert len(result["pod"]["mounts"]["cinder_volume"]["volumeMounts"]) == 2

    def test_no_backup(self):
        storage = {
            **DEFAULT_STORAGE,
            "backups": {"type": "none"},
        }
        result = storage_to_cinder_helm_values(storage)
        assert result["manifests"]["deployment_backup"] is False

    def test_mixed_ceph_and_non_ceph_backends(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "powerstore": {
                        "type": "powerstore",
                        "ip": "10.0.0.1",
                        "login": "admin",
                        "password": "secret",
                        "protocol": "iscsi",
                    },
                },
            },
        }
        result = storage_to_cinder_helm_values(storage)

        # Mixed: Ceph wins as storage type
        assert result["storage"] == "ceph"
        assert "rbd1" in result["conf"]["backends"]
        assert "powerstore" in result["conf"]["backends"]
        assert result["conf"]["enable_iscsi"] is True
        assert result["conf"]["cinder"]["DEFAULT"]["enabled_backends"] == "rbd1,powerstore"
        # Ceph pools still generated for the rbd backend
        assert "cinder.volumes" in result["conf"]["ceph"]["pools"]
        # storage-init NOT disabled (has ceph backends)
        assert result.get("manifests", {}).get("job_storage_init") is not False

    def test_non_ceph_volumes_with_ceph_backup(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "powerstore",
                "backends": {
                    "powerstore": {
                        "type": "powerstore",
                        "ip": "10.0.0.1",
                        "login": "admin",
                        "password": "secret",
                        "protocol": "iscsi",
                    }
                },
            },
            "backups": DEFAULT_STORAGE["backups"],
        }
        result = storage_to_cinder_helm_values(storage)

        # Backup pool generated even without Ceph volume backends
        assert "ceph" in result["conf"]
        assert "backup" in result["conf"]["ceph"]["pools"]
        assert result["conf"]["ceph"]["pools"]["backup"]["app_name"] == "cinder-backup"
        assert result["conf"]["cinder"]["DEFAULT"]["backup_driver"] == (
            "cinder.backup.drivers.ceph.CephBackupDriver"
        )


class TestStorageToGlanceHelmValues:
    def test_single_rbd_backend(self):
        result = storage_to_glance_helm_values(DEFAULT_STORAGE)
        assert result["storage"] == "rbd"
        glance_store = result["conf"]["glance"]["glance_store"]
        assert glance_store["rbd_store_pool"] == "glance.images"
        assert glance_store["rbd_store_user"] == "glance"

    def test_multi_backend_with_cinder(self):
        storage = {
            **DEFAULT_STORAGE,
            "images": {
                "default": "rbd1",
                "backends": {
                    "rbd1": {
                        "type": "rbd",
                        "pool": "glance.images",
                        "ceph_user": "glance",
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
        assert glance_conf["cinder_store"]["cinder_catalog_info"] == "volumev3::internalURL"

        # Cinder store needs privileged access
        assert result["pod"]["security_context"]["glance"]["container"]["glance_api"]["privileged"] is True

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
        assert "storage" not in result  # No rbd storage type
        assert result["pod"]["useHostNetwork"] == {"api": True}


class TestStorageToNovaHelmValues:
    def test_rbd_ephemeral(self):
        result = storage_to_nova_helm_values(DEFAULT_STORAGE)
        assert result["conf"]["ceph"]["enabled"] is True
        libvirt = result["conf"]["nova"]["libvirt"]
        assert libvirt["images_type"] == "rbd"
        assert libvirt["images_rbd_pool"] == "vms"
        assert libvirt["rbd_user"] == "cinder"
        assert libvirt["rbd_secret_uuid"] == "457eb676-33da-42ec-9a8c-9293d545c337"

    def test_local_ephemeral(self):
        storage = {
            **DEFAULT_STORAGE,
            "ephemeral": {"type": "local"},
        }
        result = storage_to_nova_helm_values(storage)
        assert result["conf"]["ceph"]["enabled"] is False
        assert result["conf"]["nova"]["libvirt"]["images_type"] == "qcow2"

    def test_iscsi_from_volume_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "powerstore",
                "backends": {
                    "powerstore": {
                        "type": "powerstore",
                        "ip": "10.0.0.1",
                        "login": "admin",
                        "password": "secret",
                        "protocol": "iscsi",
                    }
                },
            },
        }
        result = storage_to_nova_helm_values(storage)
        assert result["conf"]["enable_iscsi"] is True

    def test_mixed_ceph_ephemeral_and_non_ceph_volumes(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "powerstore": {
                        "type": "powerstore",
                        "ip": "10.0.0.1",
                        "login": "admin",
                        "password": "secret",
                        "protocol": "iscsi",
                    },
                },
            },
        }
        result = storage_to_nova_helm_values(storage)
        # Ceph ephemeral still enabled
        assert result["conf"]["ceph"]["enabled"] is True
        assert result["conf"]["nova"]["libvirt"]["images_type"] == "rbd"
        # iSCSI also enabled for non-Ceph volume backend
        assert result["conf"]["enable_iscsi"] is True


class TestStorageToLibvirtHelmValues:
    def test_default_ceph(self):
        result = storage_to_libvirt_helm_values(DEFAULT_STORAGE)
        assert result["conf"]["ceph"]["enabled"] is True
        assert result["conf"]["ceph"]["cinder"]["user"] == "cinder"
        assert result["conf"]["ceph"]["cinder"]["secret_uuid"] == "457eb676-33da-42ec-9a8c-9293d545c337"

    def test_additional_users_for_ec_backend(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "rbd_ec": {
                        "type": "rbd-ec",
                        "pool": "cinder.volumes.ec",
                        "erasure_coded": {
                            "k": 4,
                            "m": 2,
                            "failure_domain": "host",
                        },
                        "metadata_replication": 3,
                        "ceph_user": "cinder-ec",
                        "secret_uuid": "808c5658-7c46-4818-8f26-82a217e3a57a",
                    },
                },
            },
        }
        result = storage_to_libvirt_helm_values(storage)
        additional = result["conf"]["ceph"]["additional_users"]
        assert len(additional) == 1
        assert additional[0]["user"] == "cinder-ec"
        assert additional[0]["secret_uuid"] == "808c5658-7c46-4818-8f26-82a217e3a57a"
        assert additional[0]["secret_name"] == "cinder-volume-rbd-keyring-rbd_ec"

    def test_no_ceph(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "powerstore",
                "backends": {
                    "powerstore": {
                        "type": "powerstore",
                        "ip": "10.0.0.1",
                        "login": "admin",
                        "password": "secret",
                        "protocol": "iscsi",
                    }
                },
            },
            "ephemeral": {"type": "local"},
        }
        result = storage_to_libvirt_helm_values(storage)
        assert result["conf"]["ceph"]["enabled"] is False

    def test_mixed_ceph_and_non_ceph_volumes(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "powerstore": {
                        "type": "powerstore",
                        "ip": "10.0.0.1",
                        "login": "admin",
                        "password": "secret",
                        "protocol": "iscsi",
                    },
                },
            },
        }
        result = storage_to_libvirt_helm_values(storage)
        # Ceph enabled because default volume backend is Ceph
        assert result["conf"]["ceph"]["enabled"] is True
        assert result["conf"]["ceph"]["cinder"]["user"] == "cinder"


class TestStorageToCephProvisionersHelmValues:
    def test_no_ec_backends(self):
        result = storage_to_ceph_provisioners_helm_values(DEFAULT_STORAGE)
        assert result == {}

    def test_ec_backend_generates_client_conf(self):
        storage = {
            **DEFAULT_STORAGE,
            "volumes": {
                "default": "rbd1",
                "backends": {
                    "rbd1": DEFAULT_STORAGE["volumes"]["backends"]["rbd1"],
                    "rbd_ec": {
                        "type": "rbd-ec",
                        "pool": "cinder.volumes.ec",
                        "erasure_coded": {
                            "k": 4,
                            "m": 2,
                            "failure_domain": "host",
                        },
                        "metadata_replication": 3,
                        "ceph_user": "cinder-ec",
                        "secret_uuid": "808c5658-7c46-4818-8f26-82a217e3a57a",
                    },
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
                    "rbd_ec": {
                        "type": "rbd-ec",
                        "pool": "cinder.volumes.ec",
                        "data_pool": "custom-data",
                        "erasure_coded": {
                            "k": 4,
                            "m": 2,
                            "failure_domain": "host",
                        },
                        "metadata_replication": 3,
                        "ceph_user": "cinder-ec",
                        "secret_uuid": "808c5658-7c46-4818-8f26-82a217e3a57a",
                    },
                },
            },
        }
        result = storage_to_ceph_provisioners_helm_values(storage)
        client = result["conf"]["ceph"]["client.cinder-ec"]
        assert client["rbd default data pool"] == "custom-data"
