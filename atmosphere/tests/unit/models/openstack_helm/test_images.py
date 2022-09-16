import confspirator

from atmosphere.config import CONF
from atmosphere.models.openstack_helm import images as osh_images


def test_images_for_chart_memcached_with_defaults():
    assert {
        "pull_policy": "Always",
        "tags": {
            "memcached": CONF.images.memcached,
            "prometheus_memcached_exporter": CONF.images.memcached_exporter,
        },
    } == osh_images.Images.for_chart("memcached").to_primitive()


@confspirator.modify_conf(
    CONF,
    {
        "atmosphere.images.memcached": [{"operation": "override", "value": "foo"}],
        "atmosphere.images.memcached_exporter": [
            {"operation": "override", "value": "bar"}
        ],
    },
)
def test_images_for_chart_memcached_with_overrides():
    assert {
        "pull_policy": "Always",
        "tags": {
            "memcached": "foo",
            "prometheus_memcached_exporter": "bar",
        },
    } == osh_images.Images.for_chart("memcached").to_primitive()
