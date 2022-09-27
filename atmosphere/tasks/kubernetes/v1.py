import pykube

from atmosphere import logger
from atmosphere.tasks.kubernetes import base

LOG = logger.get_logger()


class ApplyNamespaceTask(base.ApplyKubernetesObjectTask):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(
            pykube.Namespace,
            None,
            name,
            requires=set(["name"]),
            inject={"name": name},
            *args,
            **kwargs,
        )

    def generate_object(self, name, *args, **kwargs):
        return pykube.Namespace(
            self.api,
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": name},
            },
        )


class ApplyServiceTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, labels: dict, spec: dict):
        super().__init__(
            pykube.Service,
            namespace,
            name,
            requires=set(["namespace", "name", "labels", "spec"]),
            inject={"name": name, "labels": labels, "spec": spec},
        )

    def generate_object(
        self,
        namespace: pykube.Namespace,
        name: str,
        labels: dict,
        spec: dict,
        *args,
        **kwargs,
    ) -> pykube.Service:
        return pykube.Service(
            self.api,
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": name,
                    "namespace": namespace.name,
                    "labels": labels,
                },
                "spec": spec,
            },
        )


class ApplySecretTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, data: str, *args, **kwargs):
        super().__init__(
            pykube.Secret,
            namespace,
            name,
            requires=set(["namespace", "name", "data"]),
            inject={"name": name, "data": data},
            *args,
            **kwargs,
        )

    def generate_object(
        self, namespace: pykube.Namespace, name: str, data: dict, *args, **kwargs
    ):
        return pykube.Secret(
            self.api,
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": name,
                    "namespace": namespace.name,
                },
                "data": data,
            },
        )
