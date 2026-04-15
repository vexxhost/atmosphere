# `smartctl_exporter`

Deploys the `prometheus-smartctl-exporter` Helm chart as a DaemonSet on
bare-metal nodes to expose disk SMART metrics for Prometheus scraping.

## Role variables

| Variable | Default | Description |
|---|---|---|
| `smartctl_exporter_helm_release_name` | `prometheus-smartctl-exporter` | Helm release name |
| `smartctl_exporter_helm_release_namespace` | `monitoring` | Namespace to deploy into |
| `smartctl_exporter_helm_values` | `{}` | Extra Helm values to merge |

To exclude specific devices from monitoring:

```yaml
smartctl_exporter_helm_values:
  config:
    device_exclude: /dev/sr.*
```
