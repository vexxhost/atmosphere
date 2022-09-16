from atmosphere.config import CONF
from atmosphere.models.openstack_helm import endpoints as osh_endpoints


def test_endpoint_for_chart_memcached():
    endpoints = osh_endpoints.Endpoints.for_chart("memcached")

    assert {
        "oslo_cache": {
            "auth": {
                "memcache_secret_key": CONF.memcached.secret_key,
            }
        }
    } == endpoints.to_primitive()
