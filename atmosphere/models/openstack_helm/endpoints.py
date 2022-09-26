from schematics import types

from atmosphere.config import CONF
from atmosphere.models import base


class Endpoint(base.Model):
    pass


class EndpointHosts(base.Model):
    default = types.StringType()


class OsloCacheEndpointAuth(base.Model):
    memcache_secret_key = types.StringType(required=True)


class OsloCacheEndpoint(Endpoint):
    auth = types.ModelType(OsloCacheEndpointAuth)

    @classmethod
    def for_chart(cls, chart):
        return cls(
            {
                "auth": OsloCacheEndpointAuth(
                    {
                        "memcache_secret_key": CONF.memcached.secret_key,
                    }
                )
            }
        )


class OsloDbEndpointHosts(EndpointHosts):
    default = types.StringType(default="percona-xtradb-haproxy")


class OsloDbEndpointAuthUser(base.Model):
    username = types.StringType()
    password = types.StringType()


class OsloDbEndpointAuth(base.Model):
    keystone = types.ModelType(OsloDbEndpointAuthUser)


class OsloDbEndpoint(Endpoint):
    auth = types.ModelType(OsloDbEndpointAuth)
    hosts = types.ModelType(OsloDbEndpointHosts, default=OsloDbEndpointHosts())

    @classmethod
    def for_chart(cls, chart):
        pass


class Endpoints(base.Model):
    oslo_cache = types.ModelType(OsloCacheEndpoint)
    oslo_db = types.ModelType(OsloDbEndpoint)

    MAPPINGS = {
        "oslo_cache": OsloCacheEndpoint,
        "oslo_db": OsloDbEndpoint,
    }

    ENDPOINTS = {
        "memcached": ["oslo_cache"],
    }

    @classmethod
    def for_chart(cls, chart):
        endpoint = cls()

        for endpoint_name in cls.ENDPOINTS[chart]:
            endpoint[endpoint_name] = cls.MAPPINGS[endpoint_name].for_chart(chart)
        endpoint.validate()

        return endpoint
