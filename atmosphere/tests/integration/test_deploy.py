import pykube

from atmosphere import flows
from atmosphere.models import config


def test_kubernetes_version(flux_cluster):
    assert flux_cluster.api.version == ("1", "25")


def test_deployment(mocker, flux_cluster):
    mocker.patch("atmosphere.clients.get_pykube_api", return_value=flux_cluster.api)

    flux_cluster.kubectl("create", "namespace", "openstack")
    flux_cluster.kubectl(
        "label", "node", "pytest-kind-control-plane", "openstack-control-plane=enabled"
    )

    cfg = config.Config.get_mock_object()
    engine = flows.get_engine(cfg)
    engine.run()

    initial_memcache_secret = pykube.Secret.objects(
        flux_cluster.api, namespace="openstack"
    ).get_by_name("atmosphere-memcached")
    assert initial_memcache_secret.exists()

    cfg.memcached.secret_key = "not-secret"
    engine = flows.get_engine(cfg)
    engine.run()

    updated_memcache_secret = pykube.Secret.objects(
        flux_cluster.api, namespace="openstack"
    ).get_by_name("atmosphere-memcached")
    assert updated_memcache_secret.exists()

    assert initial_memcache_secret.obj["data"] != updated_memcache_secret.obj["data"]
