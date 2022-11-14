import pykube

from atmosphere import logger
from atmosphere.tasks.kubernetes import base

LOG = logger.get_logger()


class ApplyNamespaceTask(base.ApplyKubernetesObjectTask):
    def __init__(self, name: str):
        super().__init__(kind=pykube.Namespace, namespace=None, name=name)

    def generate_object(self) -> pykube.Namespace:
        return pykube.Namespace(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {"name": self._obj_name},
            },
        )


class ApplyServiceTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, labels: dict, spec: dict):
        self._labels = labels
        self._spec = spec

        super().__init__(
            kind=pykube.Service,
            namespace=namespace,
            name=name,
            requires=set(["namespace"]),
        )

    def generate_object(self) -> pykube.Service:
        return pykube.Service(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": self._obj_name,
                    "namespace": self._obj_namespace,
                    "labels": self._labels,
                },
                "spec": self._spec,
            },
        )


class ApplySecretTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, data: str):
        self._data = data

        super().__init__(
            kind=pykube.Secret,
            namespace=namespace,
            name=name,
            requires=set(["namespace"]),
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
