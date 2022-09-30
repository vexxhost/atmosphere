from schematics import types

from atmosphere.models import base


class ImagesTags(base.Model):
    pass


class MemcachedImagesTags(ImagesTags):
    memcached = types.StringType(required=True)
    prometheus_memcached_exporter = types.StringType(required=True)

    @classmethod
    def for_chart(cls, chart, config):
        return cls(
            {
                "memcached": config.memcached.images.memcached,
                "prometheus_memcached_exporter": config.memcached.images.exporter,
            }
        )


class Images(base.Model):
    pull_policy = types.StringType(default="Always")
    tags = types.ModelType(ImagesTags)

    MAPPINGS = {
        "memcached": MemcachedImagesTags,
    }

    @classmethod
    def for_chart(cls, chart, config):
        return cls(
            {
                "tags": cls.MAPPINGS[chart].for_chart(chart, config),
            }
        )
