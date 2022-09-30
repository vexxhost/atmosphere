from atmosphere.models import config
from atmosphere.models.openstack_helm import images as osh_images


def test_images_for_chart_memcached():
    cfg = config.Config.get_mock_object()
    assert {
        "pull_policy": "Always",
        "tags": {
            "memcached": cfg.memcached.images.memcached,
            "prometheus_memcached_exporter": cfg.memcached.images.exporter,
        },
    } == osh_images.Images.for_chart("memcached", cfg).to_primitive()
