# `openstack_exporter`

## Ironic lifecycle metrics

Ironic metrics remain disabled unless both the Ironic service and its exporter
collector are enabled:

```yaml
atmosphere_ironic_enabled: true
openstack_exporter_baremetal_enabled: true
```

Enabling the collector while Ironic is disabled fails validation. When either
option is false, the role keeps `--disable-service.baremetal` in the effective
exporter arguments.
