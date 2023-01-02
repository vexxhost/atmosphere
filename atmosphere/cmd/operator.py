import kopf

from atmosphere import clients
from atmosphere.operator import controllers  # noqa: F401
from atmosphere.operator.api import objects, types

API = clients.get_pykube_api()


@kopf.on.create(
    objects.OpenstackHelmRabbitmqCluster.version,
    objects.OpenstackHelmRabbitmqCluster.kind,
)
@kopf.on.resume(
    objects.OpenstackHelmRabbitmqCluster.version,
    objects.OpenstackHelmRabbitmqCluster.kind,
)
def create_openstack_helm_rabbitmq_cluster(namespace: str, name: str, spec: dict, **_):
    objects.OpenstackHelmRabbitmqCluster(
        api=API,
        metadata=types.ObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmRabbitmqClusterSpec(**spec),
    ).apply_rabbitmq_cluster()


@kopf.on.delete(
    objects.OpenstackHelmRabbitmqCluster.version,
    objects.OpenstackHelmRabbitmqCluster.kind,
)
def delete_openstack_helm_rabbitmq_cluster(namespace: str, name: str, spec: dict, **_):
    objects.OpenstackHelmRabbitmqCluster(
        api=API,
        metadata=types.ObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmRabbitmqClusterSpec(**spec),
    ).delete_rabbitmq_cluster()


@kopf.on.create(objects.OpenstackHelmIngress.version, objects.OpenstackHelmIngress.kind)
@kopf.on.resume(objects.OpenstackHelmIngress.version, objects.OpenstackHelmIngress.kind)
def create_openstack_helm_ingress(namespace: str, name: str, spec: dict, **_):
    objects.OpenstackHelmIngress(
        api=API,
        metadata=types.OpenstackHelmIngressObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmIngressSpec(**spec),
    ).apply_ingress()


@kopf.on.delete(objects.OpenstackHelmIngress.version, objects.OpenstackHelmIngress.kind)
def delete_openstack_helm_ingress(namespace: str, name: str, spec: dict, **_):
    objects.OpenstackHelmIngress(
        api=API,
        metadata=types.OpenstackHelmIngressObjectMeta(
            name=name,
            namespace=namespace,
        ),
        spec=types.OpenstackHelmIngressSpec(**spec),
    ).delete_ingress()
