import pykube

from atmosphere import deploy
from atmosphere.models import conf
from atmosphere.models.openstack_helm import values


def test_kubernetes_version(kind_cluster):
    assert kind_cluster.api.version == ("1", "25")


def test_deployment(kind_cluster, tmp_path):
    kind_cluster.kubectl("create", "namespace", "openstack")

    initial_path = tmp_path / "config-initial.toml"
    initial_path.write_text(
        """
    [memcached]
    secret_key = "secret"
    """
    )

    config = conf.from_file(initial_path)
    deploy.run(kind_cluster.api, config)

    initial_memcache_secret = pykube.Secret(
        kind_cluster.api, values.Values.for_chart("memcached", config).secret()
    )
    assert initial_memcache_secret.exists()

    updated_path = tmp_path / "config-updated.toml"
    updated_path.write_text(
        """
    [memcached]
    secret_key = "not-secret"
    """
    )

    config = conf.from_file(updated_path)
    deploy.run(kind_cluster.api, config)

    updated_memcache_secret = pykube.Secret(
        kind_cluster.api, values.Values.for_chart("memcached", config).secret()
    )
    assert updated_memcache_secret.exists()

    assert initial_memcache_secret.obj["data"] != updated_memcache_secret.obj["data"]
