from typing import ClassVar

import pykube
from pydantic import Field

from atmosphere.operator.api import mixins, types

# Kubernetes API


class Namespace(types.KubernetesObject):
    endpoint: ClassVar[str] = "namespaces"

    version: str = Field("v1", alias="apiVersion", const=True)
    kind: str = Field("Namespace", const=True)


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
