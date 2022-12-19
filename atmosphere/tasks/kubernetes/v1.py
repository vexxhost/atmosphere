import logging

import pykube

from atmosphere.tasks.kubernetes import base

LOG = logging.getLogger(__name__)


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
