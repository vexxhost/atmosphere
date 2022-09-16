from schematics import types

from atmosphere.models import base


class PrometheusMonitoring(base.Model):
    enabled = types.BooleanType()


class Monitoring(base.Model):
    prometheus = types.ModelType(PrometheusMonitoring)

    @classmethod
    def for_chart(cls, chart):
        if chart == "memcached":
            return Monitoring(
                {
                    "prometheus": PrometheusMonitoring(
                        {
                            "enabled": True,
                        }
                    )
                }
            )
