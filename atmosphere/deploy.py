from atmosphere.models.openstack_helm import values


def run(api, config):
    if config.memcached:
        values.Values.for_chart("memcached", config).apply(api)
