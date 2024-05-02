# Migrate from `vector-agent` guide

To deploy the chart as a `DaemonSet`, set `role: "Agent"` in your `values.yaml` or with Helm arguments.
The `tolerations` option is no longer populated with default values, to match previous behavior you
can use the following:

```yaml
tolerations:
  - key: node-role.kubernetes.io/master
    effect: NoSchedule
```

There have been a couple minor changes to the default configuration:

- Vector's API is enabled
- A `console` sink is now included
- The default `prometheus_exporter` sink was renamed from "prometheus_sink" to "prom_exporter"

To keep the original defaults, use the following `customConfig`:

```yaml
customConfig:
  data_dir: /vector-data-dir
  api:
    enabled: false
  sources:
    kubernetes_logs:
      type: kubernetes_logs
    host_metrics:
      filesystem:
        devices:
          excludes: [binfmt_misc]
        filesystems:
          excludes: [binfmt_misc]
        mountpoints:
          excludes: ["*/proc/sys/fs/binfmt_misc"]
      type: host_metrics
    internal_metrics:
      type: internal_metrics
  sinks:
    prometheus_sink:
      type: prometheus_exporter
      inputs: [host_metrics, internal_metrics]
      address: 0.0.0.0:9090
```

## Upgrading

Once you have determined the changes you need to make to your `values.yaml` the upgrade is as simple as:

```bash
helm upgrade -f values.yaml <ORIGINAL_RELEASE_NAME> vector/vector -n <ORIGINAL_NAMESPACE>
```

## Vector values

| Old parameter                                          | New parameter               | Comment                                                                                                 |
|--------------------------------------------------------|-----------------------------|---------------------------------------------------------------------------------------------------------|
| `dataVolume.hostPath.path`                             | `persistence.hostPath.path` |                                                                                                         |
| `existingConfigMap` and `extraConfigDirSources`        | `existingConfigMaps`        | All ConfigMaps in the `existingConfigMaps` list are projected into Vector's configuration directory     |
| `extraContainersPorts`                                 | `containerPorts`            | Ports will be automatically generated from `customConfig` but can be manually set with `containerPorts` |
| `globalOptions.*`                                      | ∅                           | Deprecated                                                                                              |
| `hostMetricsSource.*`                                  | ∅                           | Deprecated                                                                                              |
| `internalMetricsSource.*`                              | ∅                           | Deprecated                                                                                              |
| `image.version`, `image.base`                          | ∅                           | Only `image.tag` is now used to set the Vector tag                                                      |
| `imagePullSecrets`                                     | `image.pullSecrets`         |                                                                                                         |
| `logSchema.*`                                          | ∅                           | Deprecated                                                                                              |
| `kubernetesLogsSource.*`                               | ∅                           | Deprecated                                                                                              |
| `maxUnavailable`                                       | ∅                           | `maxUnavailable` should be passed in as part of the `updateStrategy` object                             |
| `podMonitor.additionalLabels`                          | ∅                           |                                                                                                         |
| `podMonitor.extraRelabelings`                          | `podMonitor.relabelings`    | The chart adds no default relabelings                                                                   |
| `podRollmeAnnotation` and`podValuesChecksumAnnotation` | ∅                           | Replaced by `rollWorkload`, enabled by default                                                          |
| `prometheusSink.*`                                     | ∅                           | Deprecated                                                                                              |
| `psp.enabled`                                          | `psp.create`                |                                                                                                         |
| `rbac.enabled`                                         | `rbac.create`               |                                                                                                         |
| `secrets.generic`                                      | ⚠️                          | `secrets.generic` now takes raw values rather than base64 encoded values                                |
| `sinks.*`                                              | ∅                           | Deprecated                                                                                              |
| `sources.*`                                            | ∅                           | Deprecated                                                                                              |
| `transforms.*`                                         | ∅                           | Deprecated                                                                                              |
| `updateStrategy`                                       | ⚠️                          | `updateStrategy` now takes an object instead of a string                                                |
| `vectorApi.*`                                          | ∅                           | Deprecated                                                                                              |
| `vectorSink.*`                                         | ∅                           | Deprecated                                                                                              |
