#!/usr/bin/env python3

import argparse
import functools

import requests
from docker_image import reference
from oslo_config import cfg
from oslo_log import log as logging
from ruyaml import YAML

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

SKIP_IMAGE_LIST = ["secretgen_controller"]


def get_digest(image_ref, token=None):
    url = f"https://{image_ref.domain()}/v2/{image_ref.path()}/manifests/{image_ref['tag']}"

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        r = requests.get(url, timeout=5, verify=False)
        auth_header = r.headers.get("Www-Authenticate")
        if auth_header:
            realm = auth_header.split(",")[0].split("=")[1].strip('"')

            r = requests.get(
                realm,
                timeout=5,
                params={"scope": f"repository:{image_ref.path()}:pull"},
                verify=False,
            )
            r.raise_for_status()

            headers["Authorization"] = f"Bearer {r.json()['token']}"

    try:
        headers["Accept"] = "application/vnd.docker.distribution.manifest.v2+json"

        r = requests.get(
            f"https://{image_ref.domain()}/v2/{image_ref.path()}/manifests/{image_ref['tag']}",
            timeout=5,
            headers=headers,
            verify=False,
        )
        r.raise_for_status()
        return r.headers["Docker-Content-Digest"]
    except requests.exceptions.HTTPError:
        headers["Accept"] = "application/vnd.oci.image.index.v1+json"

        r = requests.get(
            f"https://{image_ref.domain()}/v2/{image_ref.path()}/manifests/{image_ref['tag']}",
            timeout=5,
            headers=headers,
            verify=False,
        )
        r.raise_for_status()
        return r.headers["Docker-Content-Digest"]


@functools.cache
def get_pinned_image(image_src):
    image_ref = reference.Reference.parse(image_src)

    if image_ref.domain() == "registry.atmosphere.dev":
        # Get token for docker.io
        r = requests.get(
            "https://registry.atmosphere.dev/service/token",
            timeout=5,
            params={
                "service": "harbor-registry",
                "scope": f"repository:{image_ref.path()}:pull",
            },
        )
        r.raise_for_status()
        token = r.json()["token"]

        digest = get_digest(image_ref, token=token)
    elif image_ref.domain() == "quay.io":
        r = requests.get(
            f"https://quay.io/api/v1/repository/{image_ref.path()}/tag/",
            timeout=5,
            params={"specificTag": image_ref["tag"]},
        )
        r.raise_for_status()
        digest = r.json()["tags"][0]["manifest_digest"]
    elif image_ref.domain() == "docker.io":
        # Get token for docker.io
        r = requests.get(
            "https://auth.docker.io/token",
            timeout=5,
            params={
                "service": "registry.docker.io",
                "scope": f"repository:{image_ref.path()}:pull",
            },
        )
        r.raise_for_status()
        token = r.json()["token"]

        r = requests.get(
            f"https://registry-1.docker.io/v2/{image_ref.path()}/manifests/{image_ref['tag']}",
            timeout=5,
            headers={
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
                "Authorization": f"Bearer {token}",
            },
        )
        r.raise_for_status()
        digest = r.headers["Docker-Content-Digest"]
    elif image_ref.domain() == "ghcr.io":
        # Get token for docker.io
        r = requests.get(
            "https://ghcr.io/token",
            timeout=5,
            params={
                "service": "ghcr.io",
                "scope": f"repository:{image_ref.path()}:pull",
            },
        )
        r.raise_for_status()
        token = r.json()["token"]

        digest = get_digest(image_ref, token=token)
    else:
        digest = get_digest(image_ref)

    return f"{image_ref.domain()}/{image_ref.path()}:{image_ref['tag']}@{digest}"


def main():
    logging.register_options(CONF)
    logging.setup(CONF, "atmosphere-bump-images")

    parser = argparse.ArgumentParser("bump-images")
    parser.add_argument(
        "src", help="Path for default values file", type=argparse.FileType("r")
    )
    parser.add_argument(
        "dst", help="Path for output file", type=argparse.FileType("r+")
    )

    args = parser.parse_args()

    yaml = YAML(typ="rt")
    data = yaml.load(args.src)

    for image in data["_atmosphere_images"]:
        if image in SKIP_IMAGE_LIST:
            continue

        image_src = data["_atmosphere_images"][image].replace(
            "{{ atmosphere_release }}", data["atmosphere_release"]
        )
        pinned_image = get_pinned_image(image_src)

        LOG.info("Pinning image %s from %s to %s", image, image_src, pinned_image)
        data["_atmosphere_images"][image] = pinned_image

    yaml.dump(data, args.dst)


if __name__ == "__main__":
    main()
