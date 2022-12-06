import kopf

from atmosphere import clients
from atmosphere.operator.api.openstack import identity
from atmosphere.operator.controllers.openstack import utils as openstack_utils


@kopf.on.create(identity.ImpliedRole.version, identity.ImpliedRole.kind)
def create_fn(namespace: str, spec: dict, **_):
    osc = openstack_utils.get_client(namespace)
    osc._identity_client.put(url_for_implied_role(namespace, spec))


@kopf.on.delete(identity.ImpliedRole.version, identity.ImpliedRole.kind)
def delete_fn(namespace: str, spec: dict, **_):
    osc = openstack_utils.get_client(namespace)
    osc._identity_client.delete(url_for_implied_role(namespace, spec))


def url_for_implied_role(namespace: str, spec: dict):
    api = clients.get_pykube_api()

    prior_role_ref = spec.get("roleRef")
    prior_role = identity.Role.get(api, namespace, prior_role_ref["name"])

    implied_role_ref = spec.get("impliedRoleRef")
    implied_role = identity.Role.get(api, namespace, implied_role_ref["name"])

    return f"/roles/{prior_role.id}/implies/{implied_role.id}"
