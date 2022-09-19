import pykube
from taskflow import task

from atmosphere import clients, logger

LOG = logger.get_logger()


class EnsureSecretTask(task.Task):
    def execute(self, secret_namespace, secret_name, secret_data, *args, **kwargs):
        log = LOG.bind(namespace=secret_namespace, name=secret_name)
        api = clients.get_pykube_api()

        log.debug("Ensuring secret")
        secret = pykube.Secret(
            api,
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": secret_name,
                    "namespace": secret_namespace,
                },
                "data": secret_data,
            },
        )

        if not secret.exists():
            log.debug("Secret does not exist, creating")
            secret.create()

        secret.reload()

        if secret.obj["data"] != secret_data:
            log.info("Secret data has changed, updating")
            secret.obj["data"] = secret_data
            secret.update()
        else:
            log.debug("Secret is up to date")

        log.info("Ensured secret")
