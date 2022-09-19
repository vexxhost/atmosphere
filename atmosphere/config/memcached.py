import uuid

from confspirator import fields, groups

config_group = groups.ConfigGroup("memcached")

config_group.register_child_config(
    fields.BoolConfig(
        "enabled",
        default=True,
        required=True,
        help_text="Enable Atmosphere-managed Memcached",
    ),
)
config_group.register_child_config(
    fields.StrConfig(
        "secret_key",
        required=True,
        help_text="Encryption secret key",
        test_default=uuid.uuid4().hex,
    ),
)
config_group.register_child_config(
    fields.DictConfig(
        "overrides",
        help_text="Override Helm chart values",
        default={},
    )
)
