import pykube
from taskflow import task

from atmosphere import clients, logger

LOG = logger.get_logger()


class HelmRepository(pykube.objects.NamespacedAPIObject):
    version = "source.toolkit.fluxcd.io/v1beta2"
    endpoint = "helmrepositories"
    kind = "HelmRepository"


class EnsureHelmRepositoryTask(task.Task):
    def execute(self, namespace, name, url, *args, **kwargs):
        log = LOG.bind(kind="HelmRelease", namespace=namespace, name=name)
        api = clients.get_pykube_api()

        log.debug("Ensuring HelmRepository")
        repository = HelmRepository(
            api,
            {
                "apiVersion": "source.toolkit.fluxcd.io/v1beta2",
                "kind": "HelmRepository",
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                },
                "spec": {
                    "interval": "1m",
                    "url": url,
                },
            },
        )

        if not repository.exists():
            log.debug("Resource does not exist, creating")
            repository.create()
        else:
            repository.update()

        log.info("Ensured resource")
