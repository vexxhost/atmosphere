import base64

import mergedeep
import yaml
from schematics import types
from schematics.transforms import blacklist

from atmosphere.config import CONF
from atmosphere.models import base
from atmosphere.models.openstack_helm import endpoints, images, monitoring


class Values(base.Model):
    chart = types.StringType(required=True)

    endpoints = types.ModelType(endpoints.Endpoints)
    images = types.ModelType(images.Images)
    monitoring = types.ModelType(monitoring.Monitoring)

    class Options:
        roles = {"default": blacklist("chart")}

    @classmethod
    def for_chart(cls, chart):
        return cls(
            {
                "chart": chart,
                "endpoints": endpoints.Endpoints.for_chart(chart),
                "images": images.Images.for_chart(chart),
                "monitoring": monitoring.Monitoring.for_chart(chart),
            }
        )

    @property
    def secret_data(self):
        data = self.to_native()
        overrides = getattr(CONF, self.chart).overrides
        values = mergedeep.merge({}, data, overrides)
        values_yaml = yaml.dump(values, default_flow_style=False)
        return {
            "values.yaml": base64.b64encode(values_yaml.encode("utf-8")).decode("utf-8")
        }
