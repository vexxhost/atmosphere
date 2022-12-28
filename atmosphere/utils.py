import json
import os

import _jsonnet
import tomli

from atmosphere.operator import utils

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
    return utils.get_image_ref(
        image_name,
        override_registry=get_legacy_image_repository(),
    )
