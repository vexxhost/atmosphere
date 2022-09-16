import pytest
from schematics import exceptions

from atmosphere.models import conf
from atmosphere.models.openstack_helm import endpoints as osh_endpoints


def test_endpoint_for_chart_memcached():
    data = conf.AtmosphereConfig.get_mock_object()
    data.memcached.secret_key = "foobar"
    endpoints = osh_endpoints.Endpoints.for_chart("memcached", data)

    assert {
        "oslo_cache": {
            "auth": {
                "memcache_secret_key": "foobar",
            }
        }
    } == endpoints.to_primitive()


def test_endpoint_for_chart_memcached_with_no_secret_key():
    data = conf.AtmosphereConfig.get_mock_object()
    data.memcached.secret_key = None

    with pytest.raises(exceptions.DataError):
        osh_endpoints.Endpoints.for_chart("memcached", data)
