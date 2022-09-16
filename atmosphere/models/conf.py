import tomli

from schematics import types

from atmosphere.models import base


class ServiceConfig(base.Model):
    enabled = types.BooleanType(default=True)
    overrides = types.DictType(types.BaseType)


class MemcachedImagesConfig(base.Model):
    memcached = types.StringType(default="quay.io/vexxhost/memcached:1.6.9")
    prometheus_memcached_exporter = types.StringType(
        default="quay.io/vexxhost/memcached-exporter:v0.9.0-1"
    )


class MemcachedServiceConfig(ServiceConfig):
    images = types.ModelType(MemcachedImagesConfig, default=MemcachedImagesConfig())
    secret_key = types.StringType(required=True)


class AtmosphereConfig(base.Model):
    memcached = types.ModelType(
        MemcachedServiceConfig, default=MemcachedServiceConfig()
    )


def from_toml(data):
    cfg = AtmosphereConfig(toml.loads(data), validate=True)
    cfg.validate()
    return cfg


def from_file(path):
    with open(path) as f:
        return from_toml(f.read())
