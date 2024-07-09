# `kube_prometheus_stack`

## Dashboards

To add additional Grafana dashboards that are not included in the kube-prometheus-stack chart by default, you can add the JSON
files in the `files/dashboards` directory.

Each JSON file becomes a ConfigMap (with label `grafana_dashboard=1`) that is picked up by the Grafana sidecar
container automatically.
