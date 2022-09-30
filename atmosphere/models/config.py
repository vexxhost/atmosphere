import os

import tomli
from schematics import types

from atmosphere.models import base

CONFIG_FILE = os.environ.get("ATMOSPHERE_CONFIG", "/etc/atmosphere/config.toml")


class AcmeIssuerSolverConfig(base.Model):
    type = types.StringType(choices=("http", "route53"), default="http", required=True)

    @classmethod
    def _claim_polymorphic(cls, data):
        return data.get("type", cls.type.default) == cls.TYPE


class HttpAcmeIssuerSolverConfig(AcmeIssuerSolverConfig):
    TYPE = "http"


class Route53AcmeIssuerSolverConfig(AcmeIssuerSolverConfig):
    TYPE = "route53"

    access_key_id = types.StringType(required=True)
    secret_access_key = types.StringType(required=True)
    hosted_zone_id = types.StringType(required=True)


class Issuer(base.Model):
    type = types.StringType(
        choices=("self-signed", "acme"), default="acme", required=True
    )

    @classmethod
    def _claim_polymorphic(cls, data):
        return data.get("type", cls.type.default) == cls.TYPE


class AcmeIssuerConfig(Issuer):
    TYPE = "acme"

    email = types.StringType(required=True)
    server = types.URLType(default="https://acme-v02.api.letsencrypt.org/directory")
    solver = types.PolyModelType(
        [HttpAcmeIssuerSolverConfig, Route53AcmeIssuerSolverConfig], required=True
    )


class SelfSignedIssuerConfig(Issuer):
    TYPE = "self-signed"


class MemcachedImagesConfig(base.Model):
    memcached = types.StringType(default="docker.io/library/memcached:1.6.17")
    exporter = types.StringType(default="quay.io/prometheus/memcached-exporter:v0.10.0")


class MemcachedConfig(base.Model):
    enabled = types.BooleanType(default=True)
    secret_key = types.StringType(required=True)
    images = types.ModelType(MemcachedImagesConfig, default=MemcachedImagesConfig())
    overrides = types.DictType(types.BaseType(), default={})


class Config(base.Model):
    memcached = types.ModelType(
        MemcachedConfig, default=MemcachedConfig(), required=True
    )
    issuer = types.DictType(
        types.PolyModelType([AcmeIssuerConfig, SelfSignedIssuerConfig])
    )

    @classmethod
    def load_from_file(cls, path=CONFIG_FILE):
        with open(path, "rb") as fd:
            data = tomli.load(fd)
            return cls(data, validate=True)
