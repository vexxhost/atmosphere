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


# Atmosphere


class OpenstackHelmIngress(types.NamespacedKubernetesObject):
    endpoint: ClassVar[str] = "openstackhelmingresses"

    kind: str = Field(constants.KIND_OPENSTACK_HELM_INGRESS, const=True)
    metadata: types.OpenstackHelmIngressObjectMeta
    spec: types.OpenstackHelmIngressSpec

    ENDPOINT_TO_SERVICE_MAPPING: ClassVar[dict] = {
        types.OpenstackHelmIngressObjectMetaName.cloudformation: types.IngressServiceBackend(
            name="heat-cfn",
            port=types.ServiceBackendPort(number=8000),
        ),
        types.OpenstackHelmIngressObjectMetaName.clustering: types.IngressServiceBackend(
            name="senlin-api",
            port=types.ServiceBackendPort(number=8778),
        ),
        types.OpenstackHelmIngressObjectMetaName.compute: types.IngressServiceBackend(
            name="nova-api",
            port=types.ServiceBackendPort(number=8774),
        ),
        types.OpenstackHelmIngressObjectMetaName.compute_novnc_proxy: types.IngressServiceBackend(
            name="nova-novncproxy",
            port=types.ServiceBackendPort(number=6080),
        ),
        types.OpenstackHelmIngressObjectMetaName.container_infra: types.IngressServiceBackend(
            name="magnum-api",
            port=types.ServiceBackendPort(number=9511),
        ),
        types.OpenstackHelmIngressObjectMetaName.container_infra_registry: types.IngressServiceBackend(
            name="magnum-registry",
            port=types.ServiceBackendPort(number=5000),
        ),
        types.OpenstackHelmIngressObjectMetaName.dashboard: types.IngressServiceBackend(
            name="horizon-int",
            port=types.ServiceBackendPort(number=80),
        ),
        types.OpenstackHelmIngressObjectMetaName.identity: types.IngressServiceBackend(
            name="keystone-api",
            port=types.ServiceBackendPort(number=5000),
        ),
        types.OpenstackHelmIngressObjectMetaName.image: types.IngressServiceBackend(
            name="glance-api",
            port=types.ServiceBackendPort(number=9292),
        ),
        types.OpenstackHelmIngressObjectMetaName.key_manager: types.IngressServiceBackend(
            name="barbican-api",
            port=types.ServiceBackendPort(number=9311),
        ),
        types.OpenstackHelmIngressObjectMetaName.load_balancer: types.IngressServiceBackend(
            name="octavia-api",
            port=types.ServiceBackendPort(number=9876),
        ),
        types.OpenstackHelmIngressObjectMetaName.network: types.IngressServiceBackend(
            name="neutron-server",
            port=types.ServiceBackendPort(number=9696),
        ),
        types.OpenstackHelmIngressObjectMetaName.orchestration: types.IngressServiceBackend(
            name="heat-api",
            port=types.ServiceBackendPort(number=8004),
        ),
        types.OpenstackHelmIngressObjectMetaName.placement: types.IngressServiceBackend(
            name="placement-api",
            port=types.ServiceBackendPort(number=8778),
        ),
        types.OpenstackHelmIngressObjectMetaName.volumev3: types.IngressServiceBackend(
            name="cinder-api",
            port=types.ServiceBackendPort(number=8776),
        ),
    }

    @property
    def service(self):
        return self.ENDPOINT_TO_SERVICE_MAPPING[self.metadata.name]

    def apply_ingress(self) -> Ingress:
        return Ingress(
            self.api,
            {
                "apiVersion": Ingress.version,
                "kind": Ingress.kind,
                "metadata": {
                    "name": self.metadata.name,
                    "namespace": self.metadata.namespace,
                    "labels": self.metadata.labels,
                    "annotations": {
                        **{
                            "cert-manager.io/cluster-issuer": self.spec.clusterIssuer,
                        },
                        **self.metadata.annotations,
                    },
                },
                "spec": {
                    "ingressClassName": self.spec.ingressClassName,
                    "rules": [
                        {
                            "host": self.spec.host,
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "pathType": "Prefix",
                                        "backend": {
                                            "service": self.service.dict(),
                                        },
                                    },
                                ],
                            },
                        },
                    ],
                    "tls": [
                        {
                            "secretName": f"{self.service.name}-certs",
                            "hosts": [self.spec.host],
                        }
                    ],
                },
            },
        ).apply()

    def delete_ingress(self) -> None:
        ingress = Ingress.objects(
            self.api, namespace=self.metadata.namespace
        ).get_or_none(name=self.metadata.name)
        if ingress:
            ingress.delete()
