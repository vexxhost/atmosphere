import os
import sys

import confspirator
from confspirator import groups

from atmosphere.config import images, memcached

_root_config = groups.ConfigGroup("atmosphere")
_root_config.register_child_config(images.config_group)
_root_config.register_child_config(memcached.config_group)

CONFIG_FILE = os.environ.get("ATMOSPHERE_CONFIG", "/etc/atmosphere/config.toml")


def load_config(file=CONFIG_FILE):
    if "pytest" in sys.modules:
        return confspirator.load_dict(_root_config, {}, test_mode=True)

    return confspirator.load_file(_root_config, file)


CONF = load_config()
