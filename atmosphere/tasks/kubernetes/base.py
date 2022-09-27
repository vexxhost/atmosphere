import json
import re

import pykube
from taskflow import task

from atmosphere import clients, logger

CAMEL_CASE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")
LOG = logger.get_logger()


class ApplyKubernetesObjectTask(task.Task):
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
        if self.requires:
            log = log.bind(requires=list(self.requires))
        return log

    def generate_object(self, *args, **kwargs) -> pykube.objects.APIObject:
        raise NotImplementedError

    def wait_for_resource(self, resource: pykube.objects.APIObject):
        pass

    def execute(self, *args, **kwargs):
        self.logger.debug("Ensuring resource")

        resource = self.generate_object(*args, **kwargs)
        resp = resource.api.patch(
            **resource.api_kwargs(
                headers={
                    "Content-Type": "application/apply-patch+yaml",
                },
                params={
                    "fieldManager": "atmosphere-operator",
                    "force": True,
                },
                data=json.dumps(resource.obj),
            )
        )

        resource.api.raise_for_status(resp)
        resource.set_obj(resp.json())

        self.wait_for_resource(resource)

        self.logger.info("Ensured resource")

        return {
            self.name: resource,
        }
