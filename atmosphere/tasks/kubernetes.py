import re

import pykube
from taskflow import task

from atmosphere import clients, logger

CAMEL_CASE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")
LOG = logger.get_logger()


class CreateOrUpdateKubernetesObjectTask(task.Task):
    def __init__(
        self, kind: pykube.objects.APIObject, namespace: str, name: str, *args, **kwargs
    ):
        self._obj_kind = kind
        self._obj_namespace = namespace
        self._obj_name = name

        kwargs["name"] = CAMEL_CASE_PATTERN.sub("-", kind.__name__).lower()
        if namespace:
            kwargs["name"] += f"-{namespace}"
        kwargs["name"] += f"-{name}"

        if namespace:
            # kwargs.setdefault("requires", [])
            # kwargs["requires"] += [f"namespace-{namespace}"]
            kwargs.setdefault("rebind", {})
            kwargs["rebind"]["namespace"] = f"namespace-{namespace}"

        kwargs.setdefault("provides", set())
        kwargs["provides"] = kwargs["provides"].union(set([kwargs["name"]]))

        super().__init__(*args, **kwargs)

    @property
    def api(self):
        return clients.get_pykube_api()

    @property
    def logger(self):
        log = LOG.bind(
            kind=self._obj_kind.__name__,
            name=self._obj_name,
        )
        if self._obj_namespace:
            log = log.bind(namespace=self._obj_namespace)
        return log

    def generate_object(self, *args, **kwargs):
        raise NotImplementedError

    def update_object(self, resource: pykube.objects.APIObject, *args, **kwargs):
        raise NotImplementedError

    def ensure_object(self, resource: pykube.objects.APIObject, *args, **kwargs):
        self.logger.debug("Ensuring resource")

        if not resource.exists():
            self.logger.debug("Resource does not exist, creating")
            resource.create()
        else:
            resource.reload()
            self.update_object(resource, *args, **kwargs)
            resource.update()

        self.logger.info("Ensured resource")

        return {
            self.name: resource,
        }

    def execute(self, *args, **kwargs):
        resource = self.generate_object(*args, **kwargs)
        return self.ensure_object(resource, *args, **kwargs)


class CreateOrUpdateNamespaceTask(CreateOrUpdateKubernetesObjectTask):
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

    def update_object(self, resource: pykube.objects.APIObject, *args, **kwargs):
        pass


class CreateOrUpdateServiceTask(CreateOrUpdateKubernetesObjectTask):
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

    def update_object(
        self,
        resource: pykube.Service,
        labels: dict,
        spec: dict,
    ):
        resource.obj["metadata"]["labels"] = labels
        resource.obj["spec"] = spec


class CreateOrUpdateSecretTask(CreateOrUpdateKubernetesObjectTask):
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

    def update_object(
        self,
        resource: pykube.objects.APIObject,
        data: dict,
        *args,
        **kwargs,
    ):
        resource.obj["data"] = data
