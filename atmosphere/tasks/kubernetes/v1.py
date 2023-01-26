import pykube
import structlog

from atmosphere.tasks.kubernetes import base

LOG = structlog.get_logger()


class ApplySecretTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, data: str):
        self._data = data

        super().__init__(
            kind=pykube.Secret,
            namespace=namespace,
            name=name,
        )

    def generate_object(self) -> pykube.Secret:
        return pykube.Secret(
            self.api,
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": self._obj_name,
                    "namespace": self._obj_namespace,
                },
                "stringData": self._data,
            },
        )
