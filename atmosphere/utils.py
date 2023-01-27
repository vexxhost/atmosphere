import json
import os

import _jsonnet
import tomli
from docker_image import reference

from atmosphere.operator import constants

CONFIG_FILE = os.environ.get("ATMOSPHERE_CONFIG", "/etc/atmosphere/config.toml")


def load_jsonnet_from_path(path: str) -> any:
    raw = _jsonnet.evaluate_file(path)
    return json.loads(raw)


def get_legacy_image_repository(config_path: str = CONFIG_FILE) -> str or None:
    try:
        with open(config_path, "rb") as fd:
            data = tomli.load(fd)
    except FileNotFoundError:
        return None

    if data.get("image_repository", ""):
        return data["image_repository"]

    return None


def get_image_ref_using_legacy_image_repository(image_name: str) -> str:
    override_registry = get_legacy_image_repository()

    ref = reference.Reference.parse(constants.IMAGE_LIST[image_name])
    if not override_registry:
        return ref

    # NOTE(mnaser): We re-write the name of a few images to make sense of them
    #               in the context of the override registry.
    ref_name = ref.repository["path"].split("/")[-1]
    if image_name == "skopeo":
        ref_name = "skopeo-stable"

    # NOTE(mnaser): Since the attributes inside of reference.Reference are not
    #               determined during parse time, we need to re-parse the
    #               string to get the correct attributes.
    ref["name"] = "{}/{}".format(override_registry, ref_name)
    ref = reference.Reference.parse(ref.string())

    return ref
