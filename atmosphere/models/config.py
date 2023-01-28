import os

import tomli
from schematics import types
from schematics.exceptions import ValidationError

from atmosphere.models import base

CONFIG_FILE = os.environ.get("ATMOSPHERE_CONFIG", "/etc/atmosphere/config.toml")


class ChartConfig(base.Model):
    enabled = types.BooleanType(default=True, required=True)
    overrides = types.DictType(types.BaseType(), default={})


class KubePrometheusStackChartConfig(ChartConfig):
    namespace = types.StringType(default="monitoring", required=True)


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
