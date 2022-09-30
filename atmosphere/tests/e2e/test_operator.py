import glob
import posixpath
import uuid

import pykube
import pytest
import tomli_w
from jinja2 import Environment, FileSystemLoader
from python_on_whales import docker
from tenacity import Retrying, retry_if_exception_type, stop_after_delay, wait_fixed


@pytest.fixture
def docker_image():
    tag = uuid.uuid4().hex
    image = f"vexxhost/atmosphere:{tag}"
    docker.buildx.build(".", tags=[image])
    return image


def test_e2e_for_operator(tmp_path, flux_cluster, docker_image):
    flux_cluster.load_docker_image(docker_image)
    flux_cluster.kubectl(
        "label", "node", "pytest-kind-control-plane", "openstack-control-plane=enabled"
    )

    env = Environment(
        loader=FileSystemLoader("roles/atmosphere/templates"),
        extensions=["jinja2_base64_filters.Base64Filters"],
    )
    env.filters["vexxhost.atmosphere.to_toml"] = tomli_w.dumps

    args = {
        "atmosphere_image": docker_image,
        "atmosphere_config": {
            "memcached": {
                "secret_key": "foobar",
            }
        },
    }

    # NOTE(mnaser): Create namespace before anything
    file = tmp_path / "namespace.yml"
    template = env.get_template("namespace.yml")
    file.write_text(template.render(**args))
    flux_cluster.kubectl("apply", "-f", file)

    for manifest in glob.glob("roles/atmosphere/templates/*.yml"):
        filename = posixpath.basename(manifest)
        template = env.get_template(filename)

        file = tmp_path / filename
        file.write_text(template.render(**args))

        flux_cluster.kubectl("apply", "-f", file)

    flux_cluster.kubectl(
        "-n", "openstack", "rollout", "status", "deployment/atmosphere-operator"
    )

    for pod in pykube.Pod.objects(flux_cluster.api, namespace="openstack").filter(
        selector="application=atmosphere"
    ):
        for attempt in Retrying(
            retry=retry_if_exception_type(AssertionError),
            stop=stop_after_delay(300),
            wait=wait_fixed(1),
        ):
            with attempt:
                assert "successfully started" in pod.logs()

    for secret_name in ["atmosphere-config", "atmosphere-memcached"]:
        secret = pykube.Secret.objects(
            flux_cluster.api, namespace="openstack"
        ).get_by_name(secret_name)
        assert secret.exists()
