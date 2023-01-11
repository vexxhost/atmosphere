from enum import Enum
from typing import Any

import pydantic
import pykube
import validators.domain

from atmosphere.operator import constants
from atmosphere.operator.api import mixins

# Generic


class Hostname(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        field_schema.update(
            examples=["example.com"],
        )

    @classmethod
    def validate(cls, v):
        if validators.domain(v):
            return cls(v)

    def __repr__(self):
        return f"Hostname({super().__repr__()})"


# Kubernetes API


class ObjectMeta(pydantic.BaseModel):
    name: pydantic.constr(min_length=1)
    annotations: dict[str, str] = {}
    labels: dict[str, str] = {}


class NamespacedObjectMeta(ObjectMeta):
    namespace: pydantic.constr(min_length=1)


class KubernetesObject(pydantic.BaseModel, mixins.ServerSideApplyMixin):
    api: pykube.http.HTTPClient = None

    version: str = pydantic.Field(
        constants.API_VERSION_ATMOSPHERE, alias="apiVersion", const=True
    )
    metadata: ObjectMeta

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        fields = {"api": {"exclude": True}}

    @property
    def obj(self) -> dict:
        return self.dict(by_alias=True)

    def set_obj(self, *_):
        pass

    @property
    def namespace(self) -> str:
        return None

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def base(self) -> None:
        return None

    def api_kwargs(self, **kwargs):
        return pykube.objects.APIObject.api_kwargs(self, **kwargs)


class NamespacedKubernetesObject(KubernetesObject):
    metadata: NamespacedObjectMeta

    @property
    def namespace(self) -> str:
        return self.metadata.namespace


class ServiceBackendPort(pydantic.BaseModel):
    number: pydantic.conint(ge=1, le=65535)


class IngressServiceBackend(pydantic.BaseModel):
    name: pydantic.constr(min_length=1)
    port: ServiceBackendPort


class NamespacedObjectReference(pydantic.BaseModel):
    name: pydantic.constr(min_length=1)
    namespace: pydantic.constr(min_length=1) = None


class CrossNamespaceObjectReference(NamespacedObjectReference):
    kind: pydantic.constr(min_length=1)


class HelmRepositorySpec(pydantic.BaseModel):
    url: pydantic.HttpUrl
    interval: str = "60s"


class HelmChartTemplateSpec(pydantic.BaseModel):
    chart: pydantic.constr(min_length=1)
    version: pydantic.constr(min_length=1) = None
    source_ref: CrossNamespaceObjectReference = pydantic.Field(alias="sourceRef")

    class Config:
        allow_population_by_field_name = True


class HelmChartTemplate(pydantic.BaseModel):
    spec: HelmChartTemplateSpec


class HelmReleaseActionRemediation(pydantic.BaseModel):
    retries: int = 3


class HelmReleaseActionSpecCRDsPolicy(str, Enum):
    SKIP = "Skip"
    CREATE = "Create"
    CREATE_REPLACE = "CreateReplace"


class HelmReleaseActionSpec(pydantic.BaseModel):
    crds: HelmReleaseActionSpecCRDsPolicy = (
        HelmReleaseActionSpecCRDsPolicy.CREATE_REPLACE
    )
    disable_wait: bool = pydantic.Field(default=True, alias="disableWait")
    remediation: HelmReleaseActionRemediation = HelmReleaseActionRemediation()

    class Config:
        allow_population_by_field_name = True


class HelmReleaseValuesReference(pydantic.BaseModel):
    kind: pydantic.constr(min_length=1)
    name: pydantic.constr(min_length=1)
    values_key: str = pydantic.Field(default=None, alias="valuesKey")
    target_path: str = pydantic.Field(default=None, alias="targetPath")

    class Config:
        allow_population_by_field_name = True


class HelmReleaseSpec(pydantic.BaseModel):
    chart: HelmChartTemplate
    interval: str = "60s"
    depends_on: list[NamespacedObjectReference] = pydantic.Field(
        default=[], alias="dependsOn"
    )
    install: HelmReleaseActionSpec = HelmReleaseActionSpec()
    upgrade: HelmReleaseActionSpec = HelmReleaseActionSpec()
    values: dict = {}
    values_from: list[HelmReleaseValuesReference] = pydantic.Field(
        default=[], alias="valuesFrom"
    )

    class Config:
        allow_population_by_field_name = True


# Atmosphere


class OpenstackHelmIngressObjectMetaName(str, Enum):
    cloudformation = "cloudformation"
    clustering = "clustering"
    compute = "compute"
    compute_novnc_proxy = "compute-novnc-proxy"
    container_infra = "container-infra"
    container_infra_registry = "container-infra-registry"
    dashboard = "dashboard"
    identity = "identity"
    image = "image"
    key_manager = "key-manager"
    load_balancer = "load-balancer"
    network = "network"
    orchestration = "orchestration"
    placement = "placement"
    volumev3 = "volumev3"


class OpenstackHelmIngressObjectMeta(NamespacedObjectMeta):
    name: OpenstackHelmIngressObjectMetaName


class OpenstackHelmIngressSpec(pydantic.BaseModel):
    clusterIssuer: pydantic.constr(min_length=1) = "atmosphere"
    ingressClassName: pydantic.constr(min_length=1) = "atmosphere"
    host: Hostname
