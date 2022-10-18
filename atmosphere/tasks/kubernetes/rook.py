import mergedeep
import pykube

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
            requires=set(
                [
                    "namespace",
                    f"helm-release-{constants.HELM_REPOSITORY_ROOK_CEPH}-{constants.HELM_RELEASE_ROOK_CEPH_NAME}",
                ]
            ),
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


def tasks_from_config(config: config.RookCephChartConfig) -> list:
    if not config.enabled:
        return []

    values = mergedeep.merge(
        {},
        constants.HELM_RELEASE_ROOK_CEPH_VALUES,
        config.overrides,
    )

    return [
        v1.ApplyNamespaceTask(name=constants.NAMESPACE_ROOK_CEPH),
        flux.ApplyHelmRepositoryTask(
            namespace=constants.NAMESPACE_ROOK_CEPH,
            name=constants.HELM_REPOSITORY_ROOK_CEPH,
            url="https://charts.rook.io/release",
        ),
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
                "fsid": config.fsid,
                "admin-secret": config.admin_secret,
                "mon-secret": config.monitor_secret,
            },
        ),
        v1.ApplyConfigMapTask(
            namespace=constants.NAMESPACE_ROOK_CEPH,
            name="rook-ceph-mon-endpoints",
            data={
                "data": ",".join([f"{i.name}={i.address}" for i in config.monitors]),
                "mapping": "{}",
                "maxMonId": "2",
            },
        ),
        ApplyCephClusterTask(namespace="rook-ceph", name="rook-ceph"),
    ]
