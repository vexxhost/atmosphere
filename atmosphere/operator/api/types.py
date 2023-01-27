import json
from enum import Enum

import kopf
import pydantic
import pykube
import requests

from atmosphere.operator import constants

# Kubernetes API


class ObjectMeta(pydantic.BaseModel):
    name: pydantic.constr(min_length=1)
    annotations: dict[str, str] = {}
    labels: dict[str, str] = {}


class NamespacedObjectMeta(ObjectMeta):
    namespace: pydantic.constr(min_length=1)


class KubernetesObject(pydantic.BaseModel):
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

    def apply(self):
        resp = self.api.patch(
            **self.api_kwargs(
                headers={
                    "Content-Type": "application/apply-patch+yaml",
                },
                params={
                    "fieldManager": "atmosphere-operator",
                    "force": True,
                },
                data=json.dumps(self.obj),
            )
        )

        try:
            self.api.raise_for_status(resp)
        except requests.exceptions.HTTPError:
            if resp.status_code == 404:
                raise kopf.TemporaryError("CRD is not yet installed", delay=1)
            raise

        self.set_obj(resp.json())
        return self


class NamespacedKubernetesObject(KubernetesObject):
    metadata: NamespacedObjectMeta

    @property
    def namespace(self) -> str:
        return self.metadata.namespace


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
