import textwrap

import mergedeep
import pykube

from atmosphere import clients
from atmosphere.operator.api import objects, types
from atmosphere.models import config
from atmosphere.tasks import constants
from atmosphere.tasks.kubernetes import base, flux, v1


class CephCluster(pykube.objects.NamespacedAPIObject):
    version = "ceph.rook.io/v1"
    endpoint = "cephclusters"
    kind = "CephCluster"


class ApplyCephClusterTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, name: str):
        super().__init__(
            kind=CephCluster,
            namespace=namespace,
            name=name,
        )

    def generate_object(self) -> CephCluster:
        return CephCluster(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": self._obj_name,
                    "namespace": self._obj_namespace,
                },
                "spec": {
                    "dataDirHostPath": "/var/lib/rook",
                    "cephVersion": {
                        "image": "quay.io/ceph/ceph:v16.2.10",
                    },
                    "external": {
                        "enable": True,
                    },
                },
            },
        )


class CephObjectStore(pykube.objects.NamespacedAPIObject):
    version = "ceph.rook.io/v1"
    endpoint = "cephobjectstores"
    kind = "CephObjectStore"


class ApplyCephObjectStoreTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, cluster: str, name: str):
        super().__init__(
            kind=CephObjectStore,
            namespace=namespace,
            name=name,
            requires=set(
                [
                    f"ceph-cluster-{namespace}-{cluster}",
                ]
            ),
        )

    def generate_object(self) -> CephObjectStore:
        return CephObjectStore(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": self._obj_name,
                    "namespace": self._obj_namespace,
                },
                "spec": {
                    "metadataPool": {
                        "failureDomain": "host",
                        "replicated": {
                            "size": 3,
                        },
                    },
                    "dataPool": {
                        "failureDomain": "host",
                        "replicated": {
                            "size": 3,
                        },
                    },
                    "preservePoolsOnDelete": True,
                    "gateway": {
                        "port": 80,
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
                                },
                            },
                        },
                    },
                },
            },
        )


def tasks_from_config(config: config.Config) -> list:
    if not config.rook.enabled:
        return []

    values = mergedeep.merge(
        {},
        constants.HELM_RELEASE_ROOK_CEPH_VALUES,
        config.rook.overrides,
    )

    api = clients.get_pykube_api()

    objects.Namespace(
        api=api,
        metadata=types.ObjectMeta(
            name=constants.NAMESPACE_ROOK_CEPH,
        ),
    ).apply()
    objects.HelmRepository(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_REPOSITORY_ROOK_CEPH,
            namespace=constants.NAMESPACE_ROOK_CEPH,
        ),
        spec=types.HelmRepositorySpec(
            url=constants.HELM_REPOSITORY_ROOK_CEPH_URL,
        ),
    ).apply()

    return [
        flux.ApplyHelmReleaseTask(
            namespace=constants.NAMESPACE_ROOK_CEPH,
            name=constants.HELM_REPOSITORY_ROOK_CEPH,
            repository=constants.HELM_REPOSITORY_ROOK_CEPH,
            chart=constants.HELM_RELEASE_ROOK_CEPH_NAME,
            version=constants.HELM_RELEASE_ROOK_CEPH_VERSION,
            values=values,
        ),
        v1.ApplySecretTask(
            namespace=constants.NAMESPACE_ROOK_CEPH,
            name="rook-ceph-mon",
            data={
                "cluster-name": "ceph",
                "fsid": config.rook.fsid,
                "admin-secret": config.rook.admin_secret,
                "mon-secret": config.rook.monitor_secret,
            },
        ),
        v1.ApplyConfigMapTask(
            namespace=constants.NAMESPACE_ROOK_CEPH,
            name="rook-ceph-mon-endpoints",
            data={
                "data": ",".join(
                    [f"{i.name}={i.address}" for i in config.rook.monitors]
                ),
                "mapping": "{}",
                "maxMonId": "2",
            },
        ),
        v1.ApplyConfigMapTask(
            namespace=constants.NAMESPACE_ROOK_CEPH,
            name="rook-config-override",
            data={
                "config": textwrap.dedent(
                    f"""\
                    [client]
                    rgw keystone api version = 3
                    rgw keystone url =  http://keystone-api.openstack.svc.cluster.local:5000
                    rgw keystone admin user = swift
                    rgw keystone admin password = {config.rook.keystone_password}
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
                ),
            },
        ),
        ApplyCephClusterTask(namespace="rook-ceph", name="rook-ceph"),
        ApplyCephObjectStoreTask(
            namespace="rook-ceph",
            cluster="rook-ceph",
            name="rook-ceph",
        ),
        v1.ApplyIngressTask(
            namespace=constants.NAMESPACE_ROOK_CEPH,
            name="rook-ceph-rgw",
            annotations={
                "cert-manager.io/cluster-issuer": "atmosphere",
                "nginx.ingress.kubernetes.io/proxy-body-size": "0",
                "nginx.ingress.kubernetes.io/proxy-request-buffering": "off",
            },
            spec={
                "ingressClassName": "openstack",
                "rules": [
                    {
                        "host": f"object-storage.{config.domain}",
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": "rook-ceph-rgw-rook-ceph",
                                            "port": {
                                                "number": 80,
                                            },
                                        }
                                    },
                                },
                            ],
                        },
                    },
                ],
                "tls": [
                    {
                        "secretName": "swift-tls",
                        "hosts": [
                            f"object-storage.{config.domain}",
                        ],
                    },
                ],
            },
        ),
    ]
