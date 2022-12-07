import textwrap

import pykube
import pytest

from atmosphere.models import config
from atmosphere.tasks import constants
from atmosphere.tasks.kubernetes import rook


@pytest.mark.parametrize(
    "cfg_data,expected",
    [
        pytest.param(
            textwrap.dedent(
                """\
                domain = "example.com"

                [rook]
                fsid = "b5273e43-f475-4c80-b37e-c6ac18042111"
                admin_secret = "secret-for-admin"
                monitor_secret = "secret-for-monitor"
                keystone_password = "secret-for-keystone"

                [[rook.monitors]]
                name = "mon0"
                address = "1.1.1.1"

                [[rook.monitors]]
                name = "mon1"
                address = "2.2.2.2"
                """
            ),
            [
                {
                    "apiVersion": pykube.Namespace.version,
                    "kind": pykube.Namespace.kind,
                    "metadata": {
                        "name": constants.NAMESPACE_ROOK_CEPH,
                    },
                },
                {
                    "apiVersion": "source.toolkit.fluxcd.io/v1beta2",
                    "kind": "HelmRepository",
                    "metadata": {
                        "name": constants.HELM_REPOSITORY_ROOK_CEPH,
                        "namespace": constants.NAMESPACE_ROOK_CEPH,
                    },
                    "spec": {
                        "interval": "1m",
                        "url": constants.HELM_REPOSITORY_ROOK_CEPH_URL,
                    },
                },
                {
                    "apiVersion": "helm.toolkit.fluxcd.io/v2beta1",
                    "kind": "HelmRelease",
                    "metadata": {
                        "name": constants.HELM_RELEASE_ROOK_CEPH_NAME,
                        "namespace": constants.NAMESPACE_ROOK_CEPH,
                    },
                    "spec": {
                        "interval": "60s",
                        "chart": {
                            "spec": {
                                "chart": constants.HELM_RELEASE_ROOK_CEPH_NAME,
                                "sourceRef": {
                                    "kind": "HelmRepository",
                                    "name": constants.HELM_REPOSITORY_ROOK_CEPH,
                                },
                                "version": constants.HELM_RELEASE_ROOK_CEPH_VERSION,
                            }
                        },
                        "install": {"disableWait": True},
                        "upgrade": {"disableWait": True},
                        "values": constants.HELM_RELEASE_ROOK_CEPH_VALUES,
                        "valuesFrom": [],
                    },
                },
                {
                    "apiVersion": "v1",
                    "kind": "Secret",
                    "metadata": {
                        "name": "rook-ceph-mon",
                        "namespace": constants.NAMESPACE_ROOK_CEPH,
                    },
                    "stringData": {
                        "cluster-name": "ceph",
                        "fsid": "b5273e43-f475-4c80-b37e-c6ac18042111",
                        "admin-secret": "secret-for-admin",
                        "mon-secret": "secret-for-monitor",
                    },
                },
                {
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {
                        "name": "rook-ceph-mon-endpoints",
                        "namespace": constants.NAMESPACE_ROOK_CEPH,
                    },
                    "data": {
                        "data": "mon0=1.1.1.1,mon1=2.2.2.2",
                        "mapping": "{}",
                        "maxMonId": "2",
                    },
                },
                {
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {
                        "name": "rook-config-override",
                        "namespace": constants.NAMESPACE_ROOK_CEPH,
                    },
                    "data": {
                        "config": textwrap.dedent(
                            """\
                            [client]
                            rgw keystone api version = 3
                            rgw keystone url =  http://keystone-api.openstack.svc.cluster.local:5000
                            rgw keystone admin user = swift
                            rgw keystone admin password = secret-for-keystone
                            rgw_keystone admin domain = service
                            rgw_keystone admin project = service
                            rgw keystone implicit tenants = true
                            rgw keystone accepted roles = member,admin
                            rgw_keystone accepted admin roles = admin
                            rgw keystone token cache size = 0
                            rgw s3 auth use keystone = true
                            rgw swift account in url = true
                            rgw swift versioning enabled = true
                            """
                        )
                    },
                },
                {
                    "apiVersion": "ceph.rook.io/v1",
                    "kind": "CephCluster",
                    "metadata": {"name": "rook-ceph", "namespace": "rook-ceph"},
                    "spec": {
                        "cephVersion": {"image": "quay.io/ceph/ceph:v16.2.10"},
                        "dataDirHostPath": "/var/lib/rook",
                        "external": {"enable": True},
                    },
                },
                {
                    "apiVersion": "ceph.rook.io/v1",
                    "kind": "CephObjectStore",
                    "metadata": {"name": "rook-ceph", "namespace": "rook-ceph"},
                    "spec": {
                        "dataPool": {
                            "failureDomain": "host",
                            "replicated": {"size": 3},
                        },
                        "gateway": {
                            "instances": 3,
                            "placement": {
                                "nodeAffinity": {
                                    "requiredDuringSchedulingIgnoredDuringExecution": {
                                        "nodeSelectorTerms": [
                                            {
                                                "matchExpressions": [
                                                    {
                                                        "key": "openstack-control-plane",
                                                        "operator": "In",
                                                        "values": ["enabled"],
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                }
                            },
                            "port": 80,
                        },
                        "metadataPool": {
                            "failureDomain": "host",
                            "replicated": {"size": 3},
                        },
                        "preservePoolsOnDelete": True,
                    },
                },
                {
                    "apiVersion": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "metadata": {
                        "name": "rook-ceph-rgw",
                        "namespace": "rook-ceph",
                        "labels": {},
                        "annotations": {
                            "cert-manager.io/cluster-issuer": "atmosphere",
                            "nginx.ingress.kubernetes.io/proxy-body-size": "0",
                            "nginx.ingress.kubernetes.io/proxy-request-buffering": "off",
                        },
                    },
                    "spec": {
                        "ingressClassName": "openstack",
                        "rules": [
                            {
                                "host": "object-storage.example.com",
                                "http": {
                                    "paths": [
                                        {
                                            "path": "/",
                                            "pathType": "Prefix",
                                            "backend": {
                                                "service": {
                                                    "name": "rook-ceph-rgw-rook-ceph",
                                                    "port": {"number": 80},
                                                },
                                            },
                                        }
                                    ]
                                },
                            }
                        ],
                        "tls": [
                            {
                                "secretName": "swift-tls",
                                "hosts": ["object-storage.example.com"],
                            }
                        ],
                    },
                },
            ],
            id="default",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [rook]
                enabled = false
                """
            ),
            [],
            id="disabled",
        ),
    ],
)
def test_tasks_from_config(pykube, cfg_data, expected):
    cfg = config.Config.from_string(cfg_data, validate=False)
    cfg.rook.validate()
    assert [t.generate_object().obj for t in rook.tasks_from_config(cfg)] == expected
