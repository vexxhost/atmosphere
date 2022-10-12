import pykube

from atmosphere import flows


def test_kubernetes_version(flux_cluster):
    assert flux_cluster.api.version == ("1", "25")


def test_deployment(sample_config, mocker, flux_cluster):
    mocker.patch("atmosphere.clients.get_pykube_api", return_value=flux_cluster.api)

    flux_cluster.kubectl("create", "namespace", "openstack")
    flux_cluster.kubectl(
        "label", "node", "pytest-kind-control-plane", "openstack-control-plane=enabled"
    )

    engine = flows.get_engine(sample_config)
    engine.run()

    initial_memcache_secret = pykube.Secret.objects(
        flux_cluster.api, namespace="openstack"
    ).get_by_name("atmosphere-memcached")
    assert initial_memcache_secret.exists()

    sample_config.memcached.secret_key = "not-secret"
    engine = flows.get_engine(sample_config)
    engine.run()

    updated_memcache_secret = pykube.Secret.objects(
        flux_cluster.api, namespace="openstack"
    ).get_by_name("atmosphere-memcached")
    assert updated_memcache_secret.exists()

    assert initial_memcache_secret.obj["data"] != updated_memcache_secret.obj["data"]
