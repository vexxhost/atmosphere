import confspirator
import pykube

from atmosphere import deploy
from atmosphere.config import CONF
from atmosphere.models.openstack_helm import values


def test_kubernetes_version(kind_cluster):
    assert kind_cluster.api.version == ("1", "25")


def test_deployment(kind_cluster, tmp_path):
    kind_cluster.kubectl("create", "namespace", "openstack")

    deploy.run(api=kind_cluster.api)

    initial_memcache_secret = pykube.Secret(
        kind_cluster.api, values.Values.for_chart("memcached").secret()
    )
    assert initial_memcache_secret.exists()

    with confspirator.modify_conf(
        CONF,
        {
            "atmosphere.memcached.secret_key": [
                {"operation": "override", "value": "not-secret"}
            ],
        },
    ):
        deploy.run(api=kind_cluster.api)

    updated_memcache_secret = pykube.Secret(
        kind_cluster.api, values.Values.for_chart("memcached").secret()
    )
    assert updated_memcache_secret.exists()

    assert initial_memcache_secret.obj["data"] != updated_memcache_secret.obj["data"]
