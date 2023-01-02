from enum import Enum
from typing import Any

import pydantic
import pykube
import validators.domain

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
    namespace: pydantic.constr(min_length=1)
    annotations: dict[str, str] = {}
    labels: dict[str, str] = {}


class KubernetesObject(pydantic.BaseModel, mixins.ServerSideApplyMixin):
    api: pykube.http.HTTPClient = None
    metadata: ObjectMeta

    class Config:
        arbitrary_types_allowed = True

    @property
    def obj(self) -> dict:
        return {
            **{
                "apiVersion": self.version,
                "kind": self.kind,
            },
            **self.dict(exclude={"api"}),
        }

    def set_obj(self, *_):
        pass

    @property
    def namespace(self) -> str:
        return self.metadata.namespace

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def base(self) -> None:
        return None

    def api_kwargs(self, **kwargs):
        return pykube.objects.APIObject.api_kwargs(self, **kwargs)


class ServiceBackendPort(pydantic.BaseModel):
    number: pydantic.conint(ge=1, le=65535)


class IngressServiceBackend(pydantic.BaseModel):
    name: pydantic.constr(min_length=1)
    port: ServiceBackendPort


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


class OpenstackHelmIngressObjectMeta(ObjectMeta):
    name: OpenstackHelmIngressObjectMetaName


class OpenstackHelmIngressSpec(pydantic.BaseModel):
    clusterIssuer: pydantic.constr(min_length=1) = "atmosphere"
    ingressClassName: pydantic.constr(min_length=1) = "atmosphere"
    host: Hostname
