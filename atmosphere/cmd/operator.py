import kopf

from atmosphere import clients
from atmosphere.operator import constants, controllers, utils  # noqa: F401
from atmosphere.operator.api import objects, types


@kopf.on.create(constants.API_VERSION_ATMOSPHERE, constants.KIND_OPENSTACK_HELM_INGRESS)
@kopf.on.resume(constants.API_VERSION_ATMOSPHERE, constants.KIND_OPENSTACK_HELM_INGRESS)
def create_openstack_helm_ingress(
    namespace: str, name: str, annotations: dict, labels: dict, spec: dict, **_
):
    api = clients.get_pykube_api()
    objects.OpenstackHelmIngress(
        api=api,
        metadata=types.OpenstackHelmIngressObjectMeta(
            name=name,
            namespace=namespace,
            annotations=utils.filter_annotations(annotations),
            labels=labels,
        ),
        spec=types.OpenstackHelmIngressSpec(**spec),
    ).apply_ingress()


@kopf.on.delete(constants.API_VERSION_ATMOSPHERE, constants.KIND_OPENSTACK_HELM_INGRESS)
def delete_openstack_helm_ingress(namespace: str, name: str, spec: dict, **_):
    api = clients.get_pykube_api()
    objects.OpenstackHelmIngress(
        api=api,
        metadata=types.OpenstackHelmIngressObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmIngressSpec(**spec),
    ).delete_ingress()
