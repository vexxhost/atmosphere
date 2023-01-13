from typing import ClassVar

import pykube
from pydantic import Field

from atmosphere.operator import constants
from atmosphere.operator.api import mixins, types

# Kubernetes API


class Namespace(types.KubernetesObject):
    endpoint: ClassVar[str] = "namespaces"

    version: str = Field("v1", alias="apiVersion", const=True)
    kind: str = Field("Namespace", const=True)


class Ingress(pykube.objects.Ingress, mixins.ServerSideApplyMixin):
    pass


class HelmRepository(types.NamespacedKubernetesObject):
    endpoint: ClassVar[str] = "helmrepositories"

    version: str = Field(
        "source.toolkit.fluxcd.io/v1beta2", alias="apiVersion", const=True
    )
    kind: str = Field("HelmRepository", const=True)
    spec: types.HelmRepositorySpec


class HelmRelease(types.NamespacedKubernetesObject):
    endpoint: ClassVar[str] = "helmreleases"

    version: str = Field(
        "helm.toolkit.fluxcd.io/v2beta1", alias="apiVersion", const=True
    )
    kind: str = Field("HelmRelease", const=True)
    spec: types.HelmReleaseSpec


class RabbitmqCluster(pykube.objects.NamespacedAPIObject, mixins.ServerSideApplyMixin):
    version = "rabbitmq.com/v1beta1"
    endpoint = "rabbitmqclusters"
    kind = "RabbitmqCluster"


# Atmosphere


class OpenstackHelmRabbitmqCluster(types.NamespacedKubernetesObject):
    endpoint: ClassVar[str] = "openstackhelmrabbitmqclusters"

    kind: str = Field(constants.KIND_OPENSTACK_HELM_RABBITMQ_CLUSTER, const=True)
    spec: types.OpenstackHelmRabbitmqClusterSpec

    def apply_rabbitmq_cluster(self):
        return RabbitmqCluster(
            self.api,
            {
                "apiVersion": RabbitmqCluster.version,
                "kind": RabbitmqCluster.kind,
                "metadata": {
                    "name": f"rabbitmq-{self.metadata.name}",
                    "namespace": self.metadata.namespace,
                    "annotations": self.metadata.annotations,
                    "labels": self.metadata.labels,
                },
                "spec": {
                    "image": self.spec.image,
                    "affinity": {
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
                    "rabbitmq": {
                        "additionalConfig": "vm_memory_high_watermark.relative = 0.9\n"
                    },
                    "resources": {
                        "requests": {"cpu": "500m", "memory": "1Gi"},
                        "limits": {"cpu": "1", "memory": "2Gi"},
                    },
                    "terminationGracePeriodSeconds": 15,
                },
            },
        ).apply()

    def delete_rabbitmq_cluster(self):
        rabbitmq_cluster = RabbitmqCluster.objects(
            self.api, namespace=self.metadata.namespace
        ).get_or_none(name=f"rabbitmq-{self.metadata.name}")
        if rabbitmq_cluster:
            rabbitmq_cluster.delete()
