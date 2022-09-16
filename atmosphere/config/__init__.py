import os
import sys

import confspirator
from confspirator import groups

from atmosphere.config import images, memcached

_root_config = groups.ConfigGroup("atmosphere")
_root_config.register_child_config(images.config_group)
_root_config.register_child_config(memcached.config_group)

CONFIG_FILE = os.environ.get('ATMOSPHERE_CONFIG', '/etc/atmosphere/config.toml')


def _load_config():
    if "pytest" in sys.modules:
        return confspirator.load_dict(_root_config, {}, test_mode=True)

    return confspirator.load_file(_root_config, CONFIG_FILE)


CONF = _load_config()
