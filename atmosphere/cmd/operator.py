import kopf
import pykube
from kopf._cogs.structs import patches

from atmosphere import clients, flows, utils
from atmosphere.models import config


@kopf.on.create("identity.atmosphere.vexxhost.com", "v1alpha1", "CatalogService")
def identity_catalog_service_create(
    namespace: str, name: str, spec: dict, patch: patches.Patch, **kwargs
):
    osc = utils.get_openstack_client(namespace)

    type = spec.get("type")
    description = spec.get("description")

    services = osc.search_services(name_or_id=name, filters={"type": type})

    if len(services) > 1:
        raise kopf.PermanentError(
            f"Found more than one service with name {name} and type {type}"
        )
    elif len(services) == 1:
        service = services[0]
    else:
        service = osc.create_service(
            name=name, type=type, description=description, enabled=True
        )

    patch.status["id"] = service.id


@kopf.on.delete("identity.atmosphere.vexxhost.com", "v1alpha1", "CatalogService")
def identity_catalog_service_delete(namespace: str, status: dict, **kwargs):
    service_id = status.get("id")
    if service_id is None:
        return

    osc = utils.get_openstack_client(namespace)
    osc.delete_service(service_id)


class CatalogService(pykube.objects.NamespacedAPIObject):
    version = "identity.atmosphere.vexxhost.com/v1alpha1"
    endpoint = "catalogservices"
    kind = "CatalogService"


@kopf.on.create("identity.atmosphere.vexxhost.com", "v1alpha1", "CatalogEndpoint")
def identity_catalog_endpoint_create(
    namespace: str, body: dict, spec: dict, patch: patches.Patch, **kwargs
):
    api = clients.get_pykube_api()
    osc = utils.get_openstack_client(namespace, api=api)

    service_ref = spec.get("serviceRef")
    service = CatalogService.objects(
        api, namespace=service_ref["namespace"]
    ).get_or_none(name=service_ref["name"])
    if service is None or service.obj["status"].get("id") is None:
        raise kopf.TemporaryError(
            f"catalogservice/{service_ref['name']} is not yet ready.", delay=5
        )

    region = spec.get("region")
    interface = spec.get("interface")
    url = spec.get("url")

    endpoints = osc.search_endpoints(
        filters={
            "service_id": service.obj["status"]["id"],
            "region": region,
            "interface": interface,
        }
    )

    if len(endpoints) > 1:
        raise kopf.PermanentError(
            f"Multiple endpoints with service_id={service.obj['status']['id']}, region={region}, interface={interface}"
        )
    elif len(endpoints) == 1:
        endpoint = endpoints[0]
    else:
        endpoint = osc.create_endpoint(
            service_name_or_id=service.obj["status"].get("id"),
            region=region,
            interface=interface,
            url=url,
        )
        # NOTE(mnaser): why?
        endpoint = endpoint[0]

    patch.status["id"] = endpoint.id


@kopf.on.startup()
def startup(**kwargs):
    cfg = config.Config.from_file()
    engine = flows.get_engine(cfg)
    engine.run()
