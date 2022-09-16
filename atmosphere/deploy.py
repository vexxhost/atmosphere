from atmosphere import clients
from atmosphere.config import CONF
from atmosphere.models.openstack_helm import values


def run(api=None):
    if not api:
        api = clients.get_pykube_api()

    if CONF.memcached.enabled:
        values.Values.for_chart("memcached").apply(api)
