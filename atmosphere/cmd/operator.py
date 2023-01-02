import kopf

from atmosphere import clients
from atmosphere.operator import constants, controllers  # noqa: F401
from atmosphere.operator.api import objects, types

API = clients.get_pykube_api()


@kopf.on.create(
    constants.API_VERSION_ATMOSPHERE,
    constants.KIND_OPENSTACK_HELM_RABBITMQ_CLUSTER,
)
@kopf.on.resume(
    constants.API_VERSION_ATMOSPHERE,
    constants.KIND_OPENSTACK_HELM_RABBITMQ_CLUSTER,
)
def create_openstack_helm_rabbitmq_cluster(namespace: str, name: str, spec: dict, **_):
    objects.OpenstackHelmRabbitmqCluster(
        api=API,
        metadata=types.NamespacedObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmRabbitmqClusterSpec(**spec),
    ).apply_rabbitmq_cluster()


@kopf.on.delete(
    constants.API_VERSION_ATMOSPHERE,
    constants.KIND_OPENSTACK_HELM_RABBITMQ_CLUSTER,
)
def delete_openstack_helm_rabbitmq_cluster(namespace: str, name: str, spec: dict, **_):
    objects.OpenstackHelmRabbitmqCluster(
        api=API,
        metadata=types.NamespacedObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmRabbitmqClusterSpec(**spec),
    ).delete_rabbitmq_cluster()


@kopf.on.create(constants.API_VERSION_ATMOSPHERE, constants.KIND_OPENSTACK_HELM_INGRESS)
@kopf.on.resume(constants.API_VERSION_ATMOSPHERE, constants.KIND_OPENSTACK_HELM_INGRESS)
def create_openstack_helm_ingress(namespace: str, name: str, spec: dict, **_):
    objects.OpenstackHelmIngress(
        api=API,
        metadata=types.OpenstackHelmIngressObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmIngressSpec(**spec),
    ).apply_ingress()


@kopf.on.delete(constants.API_VERSION_ATMOSPHERE, constants.KIND_OPENSTACK_HELM_INGRESS)
def delete_openstack_helm_ingress(namespace: str, name: str, spec: dict, **_):
    objects.OpenstackHelmIngress(
        api=API,
        metadata=types.OpenstackHelmIngressObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmIngressSpec(**spec),
    ).delete_ingress()
