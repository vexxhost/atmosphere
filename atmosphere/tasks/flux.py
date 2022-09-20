import pykube

from atmosphere import logger
from atmosphere.tasks import kubernetes

LOG = logger.get_logger()


class HelmRepository(pykube.objects.NamespacedAPIObject):
    version = "source.toolkit.fluxcd.io/v1beta2"
    endpoint = "helmrepositories"
    kind = "HelmRepository"


class CreateOrUpdateHelmRepositoryTask(kubernetes.CreateOrUpdateKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, url: str, *args, **kwargs):
        super().__init__(
            HelmRepository,
            namespace,
            name,
            requires=set(["namespace", "name", "url"]),
            inject={"name": name, "url": url},
            *args,
            **kwargs
        )

    def generate_object(
        self, namespace: pykube.Namespace, name: str, url: str, *args, **kwargs
    ):
        return HelmRepository(
            self.api,
            {
                "apiVersion": "source.toolkit.fluxcd.io/v1beta2",
                "kind": "HelmRepository",
                "metadata": {
                    "name": name,
                    "namespace": namespace.name,
                },
                "spec": {
                    "interval": "1m",
                    "url": url,
                },
            },
        )

    def update_object(
        self, resource: pykube.objects.APIObject, url: str, *args, **kwargs
    ):
        resource.obj["spec"]["url"] = url
