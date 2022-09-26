from confspirator import fields, groups

config_group = groups.ConfigGroup("images")

config_group.register_child_config(
    fields.StrConfig(
        "memcached",
        required=True,
        default="docker.io/library/memcached:1.6.17",
        help_text="Memcached image",
    ),
)
config_group.register_child_config(
    fields.StrConfig(
        "memcached_exporter",
        required=True,
        default="quay.io/prometheus/memcached-exporter:v0.10.0",
        help_text="Prometheus Memcached exporter image",
    ),
)
