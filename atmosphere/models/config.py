import os

import tomli
from schematics import types
from schematics.exceptions import ValidationError

from atmosphere.models import base

CONFIG_FILE = os.environ.get("ATMOSPHERE_CONFIG", "/etc/atmosphere/config.toml")


class AcmeIssuerSolverConfig(base.Model):
    type = types.StringType(
        choices=("http", "rfc2136", "route53"), default="http", required=True
    )

    @classmethod
    def _claim_polymorphic(cls, data):
        return data.get("type", cls.type.default) == cls.TYPE


class HttpAcmeIssuerSolverConfig(AcmeIssuerSolverConfig):
    TYPE = "http"


class Rfc2136AcmeIssuerSolverConfig(AcmeIssuerSolverConfig):
    TYPE = "rfc2136"

    nameserver = types.StringType(required=True)
    tsig_algorithm = types.StringType(required=True)
    tsig_key_name = types.StringType(required=True)
    tsig_secret = types.StringType(required=True)


class Route53AcmeIssuerSolverConfig(AcmeIssuerSolverConfig):
    TYPE = "route53"

    region = types.StringType(default="global", required=True)
    hosted_zone_id = types.StringType(required=True)
    access_key_id = types.StringType(required=True)
    secret_access_key = types.StringType(required=True)


class Issuer(base.Model):
    type = types.StringType(
        choices=("acme", "ca", "self-signed"), default="acme", required=True
    )

    @classmethod
    def _claim_polymorphic(cls, data):
        return data.get("type", cls.type.default) == cls.TYPE


class AcmeIssuerConfig(Issuer):
    TYPE = "acme"

    email = types.StringType(required=True)
    server = types.URLType(default="https://acme-v02.api.letsencrypt.org/directory")
    solver = types.PolyModelType(
        [
            HttpAcmeIssuerSolverConfig,
            Rfc2136AcmeIssuerSolverConfig,
            Route53AcmeIssuerSolverConfig,
        ],
        default=HttpAcmeIssuerSolverConfig(),
        required=True,
    )


class CaIssuerConfig(Issuer):
    TYPE = "ca"

    certificate = types.StringType(required=True)
    private_key = types.StringType(required=True)


class SelfSignedIssuerConfig(Issuer):
    TYPE = "self-signed"


class ChartConfig(base.Model):
    enabled = types.BooleanType(default=True, required=True)
    overrides = types.DictType(types.BaseType(), default={})


class KubePrometheusStackChartConfig(ChartConfig):
    namespace = types.StringType(default="monitoring", required=True)


class IngressNginxChartConfig(ChartConfig):
    namespace = types.StringType(default="openstack", required=True)


class OpsGenieConfig(base.Model):
    enabled = types.BooleanType(default=False, required=True)
    api_key = types.StringType()
    heartbeat = types.StringType()

    def validate_api_key(self, data, value):
        if data["enabled"] and not value:
            raise ValidationError(types.BaseType.MESSAGES["required"])
        return value

    def validate_heartbeat(self, data, value):
        if data["enabled"] and not value:
            raise ValidationError(types.BaseType.MESSAGES["required"])
        return value


class Config(base.Model):
    image_repository = types.StringType()
    kube_prometheus_stack = types.ModelType(
        KubePrometheusStackChartConfig, default=KubePrometheusStackChartConfig()
    )
    issuer = types.PolyModelType(
        [AcmeIssuerConfig, CaIssuerConfig, SelfSignedIssuerConfig],
        default=AcmeIssuerConfig(),
        required=True,
    )
    opsgenie = types.ModelType(OpsGenieConfig, default=OpsGenieConfig())

    @classmethod
    def from_toml(cls, data, validate=True):
        c = cls(data, validate=validate)
        if validate:
            c.validate()
        return c

    @classmethod
    def from_file(cls, path=CONFIG_FILE):
        with open(path, "rb") as fd:
            data = tomli.load(fd)
            return cls.from_toml(data)

    @classmethod
    def from_string(cls, data: str, validate=True):
        data = tomli.loads(data)
        return cls.from_toml(data, validate)
