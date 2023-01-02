import kopf

from atmosphere import clients, flows
from atmosphere.models import config
from atmosphere.operator import controllers  # noqa: F401
from atmosphere.operator.api import objects, types

API = clients.get_pykube_api()


@kopf.on.startup()
def startup(**_):
    cfg = config.Config.from_file()
    engine = flows.get_engine(cfg)
    engine.run()


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
