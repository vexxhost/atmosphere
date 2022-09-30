from schematics import types
from schematics.transforms import blacklist

from atmosphere.models import base
from atmosphere.models.openstack_helm import endpoints, images, monitoring


class Values(base.Model):
    chart = types.StringType(required=True)

    endpoints = types.ModelType(endpoints.Endpoints)
    images = types.ModelType(images.Images)
    monitoring = types.ModelType(monitoring.Monitoring)

    class Options:
        roles = {"default": blacklist("chart", "config")}

    @classmethod
    def for_chart(cls, chart, config):
        return cls(
            {
                "chart": chart,
                "endpoints": endpoints.Endpoints.for_chart(chart, config),
                "images": images.Images.for_chart(chart, config),
                "monitoring": monitoring.Monitoring.for_chart(chart, config),
            }
        )
