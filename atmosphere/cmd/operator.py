import kopf

from atmosphere import clients
from atmosphere.operator import constants, controllers, utils  # noqa: F401
from atmosphere.operator.api import objects, types


@kopf.on.create(
    constants.API_VERSION_ATMOSPHERE,
    constants.KIND_OPENSTACK_HELM_RABBITMQ_CLUSTER,
)
@kopf.on.resume(
    constants.API_VERSION_ATMOSPHERE,
    constants.KIND_OPENSTACK_HELM_RABBITMQ_CLUSTER,
)
def create_openstack_helm_rabbitmq_cluster(
    namespace: str, name: str, annotations: dict, labels: dict, spec: dict, **_
):
    api = clients.get_pykube_api()
    objects.OpenstackHelmRabbitmqCluster(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=name,
            namespace=namespace,
            annotations=utils.filter_annotations(annotations),
            labels=labels,
        ),
        spec=types.OpenstackHelmRabbitmqClusterSpec(**spec),
    ).apply_rabbitmq_cluster()


@kopf.on.delete(
    constants.API_VERSION_ATMOSPHERE,
    constants.KIND_OPENSTACK_HELM_RABBITMQ_CLUSTER,
)
def delete_openstack_helm_rabbitmq_cluster(namespace: str, name: str, spec: dict, **_):
    api = clients.get_pykube_api()
    objects.OpenstackHelmRabbitmqCluster(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmRabbitmqClusterSpec(**spec),
    ).delete_rabbitmq_cluster()
