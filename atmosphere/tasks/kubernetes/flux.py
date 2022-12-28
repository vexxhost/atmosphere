import pykube
from oslo_utils import strutils
from tenacity import retry, retry_if_result, stop_after_delay, wait_fixed

from atmosphere import logger
from atmosphere.tasks.kubernetes import base

LOG = logger.get_logger()


class HelmRepository(pykube.objects.NamespacedAPIObject):
    version = "source.toolkit.fluxcd.io/v1beta2"
    endpoint = "helmrepositories"
    kind = "HelmRepository"


class ApplyHelmRepositoryTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, url: str):
        self._url = url

        super().__init__(
            kind=HelmRepository,
            namespace=namespace,
            name=name,
            requires=set(["namespace"]),
        )

    def generate_object(self) -> HelmRepository:
        return HelmRepository(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": self._obj_name,
                    "namespace": self._obj_namespace,
                },
                "spec": {
                    "interval": "1m",
                    "url": self._url,
                },
            },
        )


class HelmRelease(pykube.objects.NamespacedAPIObject):
    version = "helm.toolkit.fluxcd.io/v2beta1"
    endpoint = "helmreleases"
    kind = "HelmRelease"


class ApplyHelmReleaseTask(base.ApplyKubernetesObjectTask):
    def __init__(
        self,
        namespace: str,
        name: str,
        chart: str,
        version: str,
        repository: str = "atmosphere",
        repository_namespace: str = "openstack",
        values: dict = {},
        values_from: list = [],
        *args,
        **kwargs,
    ):
        self._repository = repository
        self._repository_namespace = repository_namespace
        self._chart = chart
        self._version = version
        self._values = values
        self._values_from = values_from

        kwargs.setdefault("requires", set())
        kwargs["requires"] = kwargs["requires"].union(set(["repository"]))

        super().__init__(
            kind=HelmRelease,
            namespace=namespace,
            name=name,
            *args,
            **kwargs,
        )

    def generate_object(self) -> HelmRelease:
        return HelmRelease(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": self._obj_name,
                    "namespace": self._obj_namespace,
                },
                "spec": {
                    "interval": "60s",
                    "chart": {
                        "spec": {
                            "chart": self._chart,
                            "version": self._version,
                            "sourceRef": {
                                "kind": "HelmRepository",
                                "name": self._repository,
                                "namespace": self._repository_namespace,
                            },
                        }
                    },
                    "install": {
                        "crds": "CreateReplace",
                        "disableWait": True,
                    },
                    "upgrade": {
                        "crds": "CreateReplace",
                        "disableWait": True,
                    },
                    "values": self._values,
                    "valuesFrom": self._values_from,
                },
            },
        )

    @retry(
        retry=retry_if_result(lambda f: f is False),
        stop=stop_after_delay(300),
        wait=wait_fixed(1),
    )
    def wait_for_resource(self, resource: HelmRelease, *args, **kwargs) -> bool:
        resource.reload()

        conditions = {
            condition["type"]: strutils.bool_from_string(condition["status"])
            for condition in resource.obj["status"].get("conditions", [])
        }

        return conditions.get("Ready", False) and conditions.get("Released", False)
