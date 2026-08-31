# `ironic`

The Ironic role deploys the OpenStack Bare Metal service. It is available from
the standard `playbooks/openstack.yml` workflow but remains disabled by
default.

Enable it in inventory variables:

```yaml
atmosphere_ironic_enabled: true
```

The playbook condition uses `default(false)`, so inventories that do not define
the variable retain the existing deployment behavior.

## Hardware sensor metrics

Hardware sensor collection is separately disabled by default. Enable it only
when the selected Ironic runtime image includes upstream
`ironic-prometheus-exporter` and uWSGI:

```yaml
atmosphere_ironic_enabled: true
ironic_prometheus_exporter_enabled: true
ironic_prometheus_exporter_sensor_interval: 600
ironic_prometheus_exporter_collect_undeployed_nodes: false
```

The role appends the `prometheus_exporter` notification driver to any existing
string, list, or Helm toolkit `multistring` driver configuration. It does not
replace existing drivers or their notification transport. Each conductor pod
runs an exporter through the chart's generic `conductor.extraContainers` hook
and shares a pod-local metrics directory through the generic conductor mount
hooks. Existing extra containers, volume mounts, and volumes are retained.
The names `ironic-prometheus-exporter` and `ironic-prometheus-metrics`, and the
mount path `/var/lib/ironic/metrics`, are reserved while the integration is
enabled so conflicting definitions fail before Helm runs.

The exporter reuses the exact image selected for `ironic_conductor`; that image
must provide the notification driver, HTTP application, and uWSGI. Resource
requests and limits can be adjusted with
`ironic_prometheus_exporter_resources`. The generic upstream example is
proposed in
[`openstack/openstack-helm` change 1002515](https://review.opendev.org/c/openstack/openstack-helm/+/1002515).

Active-node-only sensor alerts also require lifecycle collection:

```yaml
openstack_exporter_baremetal_enabled: true
```
