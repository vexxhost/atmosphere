import kopf
from kopf._cogs.structs import patches

from atmosphere.operator.api.openstack import identity
from atmosphere.operator.controllers.openstack import utils as openstack_utils


@kopf.on.create(identity.Role.version, identity.Role.kind)
def create_fn(namespace: str, name: str, spec: dict, patch: patches.Patch, **_):
    osc = openstack_utils.get_client(namespace)

    # NOTE(mnaser): Some of the roles that we create are not RFC 1123 compliant
    #               so we need to use the name from the spec instead of the
    #               name from the metadata.
    role_name = spec.get("roleName", name)

    role = osc.identity.find_role(role_name)
    if role is None:
        role = osc.identity.create_role(name=role_name)

    patch.status["id"] = role.id


@kopf.on.delete(identity.Role.version, identity.Role.kind)
def delete_fn(namespace: str, status: dict, **_):
    role_id = status.get("id")
    if role_id is None:
        return

    osc = openstack_utils.get_client(namespace)
    osc.identity.delete_role(role_id)
