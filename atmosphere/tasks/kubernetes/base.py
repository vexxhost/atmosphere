import json
import logging
import re

import pykube
from taskflow import task

from atmosphere import clients

CAMEL_CASE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")
LOG = logging.getLogger(__name__)


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

    def _log(self, resource: pykube.objects.APIObject, message: str):
        resource_info = {
            "kind": resource.kind,
        }

        resource_info["name"] = resource.name
        if resource.namespace:
            resource_info["namespace"] = resource.namespace

        # Generate user friendly string from resource info
        resource_info_str = ", ".join([f"{k}={v}" for k, v in resource_info.items()])
        LOG.info(f"[{resource_info_str}] {message}")

    def generate_object(self, *args, **kwargs) -> pykube.objects.APIObject:
        raise NotImplementedError

    def wait_for_resource(self, resource: pykube.objects.APIObject):
        pass

    def execute(self, *args, **kwargs):
        resource = self.generate_object()
        self._log(resource, "Ensuring resource")

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

        self._log(resource, "Ensured resource")

        return {
            self.name: resource,
        }
