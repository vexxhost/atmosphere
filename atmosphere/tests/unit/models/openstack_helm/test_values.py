from atmosphere.models import config
from atmosphere.models.openstack_helm import values as osh_values


class TestMemcachedValues:
    def test_values_for_chart(self):
        cfg = config.Config.get_mock_object()
        values = osh_values.Values.for_chart("memcached", cfg)

        assert {
            "endpoints": {
                "oslo_cache": {
                    "auth": {"memcache_secret_key": cfg.memcached.secret_key}
                }
            },
            "images": {
                "pull_policy": "Always",
                "tags": {
                    "memcached": cfg.memcached.images.memcached,
                    "prometheus_memcached_exporter": cfg.memcached.images.exporter,
                },
            },
            "monitoring": {
                "prometheus": {
                    "enabled": True,
                }
            },
        } == values.to_primitive()
