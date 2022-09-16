import uuid

from atmosphere.models import conf
from atmosphere.models.openstack_helm import images as osh_images


def test_images_for_chart_memcached_with_defaults():
    data = conf.AtmosphereConfig.get_mock_object()
    images = osh_images.Images.for_chart("memcached", data)

    assert {
        "pull_policy": "Always",
        "tags": {
            "memcached": data.memcached.images.memcached,
            "prometheus_memcached_exporter": data.memcached.images.prometheus_memcached_exporter,
        },
    }, images.to_primitive()


def test_images_for_chart_memcached_with_overrides():
    data = conf.AtmosphereConfig.get_mock_object()
    data.memcached.images.memcached = "foo"
    data.memcached.images.prometheus_memcached_exporter = "bar"

    images = osh_images.Images.for_chart("memcached", data)

    assert {
        "pull_policy": "Always",
        "tags": {
            "memcached": "foo",
            "prometheus_memcached_exporter": "bar",
        },
    }, images.to_primitive()
