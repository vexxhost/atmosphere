import confspirator
import pykube
import taskflow.engines

from atmosphere import flows
from atmosphere.config import CONF
from atmosphere.models.openstack_helm import values


def test_kubernetes_version(kind_cluster):
    assert kind_cluster.api.version == ("1", "25")


def test_deployment(mocker, kind_cluster):
    mocker.patch("atmosphere.clients.get_pykube_api", return_value=kind_cluster.api)

    kind_cluster.kubectl("create", "namespace", "openstack")

    engine = taskflow.engines.load(flows.DEPLOY)
    engine.run()

    initial_memcache_secret = pykube.Secret.objects(
        kind_cluster.api, namespace="openstack"
    ).get_by_name("atmosphere-memcached")
    assert initial_memcache_secret.exists()

    with confspirator.modify_conf(
        CONF,
        {
            "atmosphere.memcached.secret_key": [
                {"operation": "override", "value": "not-secret"}
            ],
        },
    ):
        engine = taskflow.engines.load(flows.DEPLOY)
        engine.run()

    updated_memcache_secret = pykube.Secret.objects(
        kind_cluster.api, namespace="openstack"
    ).get_by_name("atmosphere-memcached")
    assert updated_memcache_secret.exists()

    assert initial_memcache_secret.obj["data"] != updated_memcache_secret.obj["data"]
