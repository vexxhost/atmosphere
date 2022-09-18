import glob
import posixpath
import uuid

import pykube
import pytest
import toml
from jinja2 import Environment, FileSystemLoader
from python_on_whales import docker


@pytest.fixture
def docker_image():
    tag = uuid.uuid4().hex
    image = f"vexxhost/atmosphere:{tag}"
    docker.buildx.build(".", tags=[image])
    return image


def test_e2e_for_operator(tmp_path, kind_cluster, docker_image):
    kind_cluster.load_docker_image(docker_image)
    kind_cluster.kubectl(
        "label", "node", "pytest-kind-control-plane", "openstack-control-plane=enabled"
    )

    env = Environment(
        loader=FileSystemLoader("roles/atmosphere/templates"),
        extensions=["jinja2_base64_filters.Base64Filters"],
    )
    env.filters["to_toml"] = toml.dumps

    args = {
        "atmosphere_image": docker_image,
        "atmosphere_config": {
            "atmosphere": {
                "memcached": {
                    "secret_key": "foobar",
                }
            }
        },
    }

    # NOTE(mnaser): Create namespace before anything
    file = tmp_path / "namespace.yml"
    template = env.get_template("namespace.yml")
    file.write_text(template.render(**args))
    kind_cluster.kubectl("apply", "-f", file)

    for manifest in glob.glob("roles/atmosphere/templates/*.yml"):
        filename = posixpath.basename(manifest)
        template = env.get_template(filename)

        file = tmp_path / filename
        file.write_text(template.render(**args))

        kind_cluster.kubectl("apply", "-f", file)

    kind_cluster.kubectl(
        "-n", "openstack", "rollout", "status", "deployment/atmosphere-operator"
    )

    for pod in pykube.Pod.objects(kind_cluster.api, namespace="openstack").filter(
        selector="application=atmosphere"
    ):
        assert "successfully started" in pod.logs()

    for secret_name in ["atmosphere-config", "atmosphere-memcached"]:
        secret = pykube.Secret.objects(
            kind_cluster.api, namespace="openstack"
        ).get_by_name(secret_name)
        assert secret.exists()
