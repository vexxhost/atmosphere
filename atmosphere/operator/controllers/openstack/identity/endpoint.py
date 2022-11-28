import kopf
from kopf._cogs.structs import patches, references

from atmosphere import clients
from atmosphere.operator.api.openstack import identity
from atmosphere.operator.controllers.openstack import utils as openstack_utils


@kopf.on.validate(
    identity.Endpoint.version,
    identity.Endpoint.kind,
    operation="UPDATE",
)
def disallow_endpoint_update(resource: references.Resource, **_):
    raise kopf.AdmissionError(f"{resource.kind} is immutable.")


@kopf.on.create(identity.Endpoint.version, identity.Endpoint.kind)
def create_fn(namespace: str, spec: dict, patch: patches.Patch, **_):
    api = clients.get_pykube_api()
    osc = openstack_utils.get_client(namespace)

    service_ref = spec.get("serviceRef")
    service = identity.Service.get(api, namespace, service_ref["name"])

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
        )[0]

    # TODO: make endpoint owned by service

    patch.status["id"] = endpoint.id


@kopf.on.delete(identity.Endpoint.version, identity.Endpoint.kind)
def delete_fn(namespace: str, status: dict, **_):
    endpoint_id = status.get("id")
    if endpoint_id is None:
        return

    osc = openstack_utils.get_client(namespace)
    osc.delete_endpoint(endpoint_id)
