import uuid

import pytest
from schematics import exceptions

from atmosphere.models import conf

MEMCACHE_SECRET_KEY = uuid.uuid4().hex

VALID_CONFIG = f"""
[memcached]
secret_key = "{MEMCACHE_SECRET_KEY}"
"""


def test_from_toml_with_valid_configuration():
    try:
        data = conf.from_toml(VALID_CONFIG)
    except exceptions.DataError:
        pytest.fail("Failed to parse valid configuration")

    assert data.memcached.secret_key == MEMCACHE_SECRET_KEY


def test_from_toml_with_invalid_configuration():
    with pytest.raises(exceptions.DataError):
        conf.from_toml("")


def test_from_file_with_valid_configuration(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(VALID_CONFIG)

    try:
        data = conf.from_file(path)
    except exceptions.DataError:
        pytest.fail("Failed to parse valid configuration")

    assert data.memcached.secret_key == MEMCACHE_SECRET_KEY


def test_from_file_with_invalid_configuration(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("")

    with pytest.raises(exceptions.DataError):
        conf.from_file(path)


def test_from_file_with_missing_file(tmp_path):
    path = tmp_path / "config.toml"

    with pytest.raises(FileNotFoundError):
        conf.from_file(path)
