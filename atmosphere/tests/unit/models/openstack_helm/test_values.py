import confspirator
import pykube
import pytest

from atmosphere.config import CONF
from atmosphere.models.openstack_helm import values as osh_values


class TestMemcachedValues:
    def test_values_for_chart(self):
        values = osh_values.Values.for_chart("memcached")

        assert {
            "endpoints": {
                "oslo_cache": {
                    "auth": {"memcache_secret_key": CONF.memcached.secret_key}
                }
            },
            "images": {
                "pull_policy": "Always",
                "tags": {
                    "memcached": CONF.images.memcached,
                    "prometheus_memcached_exporter": CONF.images.memcached_exporter,
                },
            },
            "monitoring": {
                "prometheus": {
                    "enabled": True,
                }
            },
        } == values.to_primitive()
