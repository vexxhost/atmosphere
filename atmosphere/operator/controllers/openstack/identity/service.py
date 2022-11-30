import kopf
from kopf._cogs.structs import patches

from atmosphere.operator.api.openstack import identity
from atmosphere.operator.controllers.openstack import utils as openstack_utils


@kopf.on.create(identity.Service.version, identity.Service.kind)
def create_fn(namespace: str, name: str, spec: dict, patch: patches.Patch, **_):
    osc = openstack_utils.get_client(namespace)

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


@kopf.on.delete(identity.Service.version, identity.Service.kind)
def delete_fn(namespace: str, status: dict, **_):
    service_id = status.get("id")
    if service_id is None:
        return

    osc = openstack_utils.get_client(namespace)
    osc.delete_service(service_id)
