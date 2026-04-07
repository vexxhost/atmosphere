# Migrate from `vector-aggregator` guide

By default, the chart will deploy Vector as a `StatefulSet` and the default `role` option should remain "Aggregator".

There have been a number of changes to the default configuration:

- Vector's API is enabled
- A `datadog_agent` source is now included
- A `fluent` source is now included
- A `logstash` source is now included
- A `splunk_hec` source is now included
- A `statsd` source is now included
- A `syslog` source is now included
- A `console` sink is now included
- The default `prometheus_exporter` sink was renamed from "prometheus_sink" to "prom_exporter"

To keep the original defaults, use the following `customConfig`:

```yaml
customConfig:
  data_dir: /vector-data-dir
  api:
    enabled: false
  sources:
    vector:
      address: 0.0.0.0:9000
      type: vector
      version: "2"
    internal_metrics:
      type: internal_metrics
  sinks:
    prometheus_sink:
      type: prometheus_exporter
      inputs: [internal_metrics]
      address: 0.0.0.0:9090
```

## Upgrading

Once you have determined the changes you need to make to your `values.yaml` the upgrade is as simple as:

```bash
helm upgrade -f values.yaml <ORIGINAL_RELEASE_NAME> vector/vector -n <ORIGINAL_NAMESPACE>
```

## Vector values

| Old parameter                                          | New parameter                  | Comment                                                                                                     |
|--------------------------------------------------------|--------------------------------|-------------------------------------------------------------------------------------------------------------|
| `existingConfigMap` and `extraConfigDirSources`        | `existingConfigMaps`           | All ConfigMaps in the `existingConfigMaps` list are projected into Vector's configuration directory         |
| `extraContainersPorts`                                 | `containerPorts`               | Ports will be automatically generated from `customConfig` but can be manually set with `containerPorts`     |
| `global.clusterDomain` and `global.kubeDNSAddress`     | ∅                              | The paramters are set by default or by `haproxy.customConfig` or `haproxy.existingConfigMap`                |
| `globalOptions.*`                                      | ∅                              | Deprecated                                                                                                  |
| `internalMetricsSource.*`                              | ∅                              | Deprecated                                                                                                  |
| `image.version`, `image.base`                          | ∅                              | Only `image.tag` is now used to set the Vector tag                                                          |
| `imagePullSecrets`                                     | `image.pullSecrets`            |                                                                                                             |
| `logSchema.*`                                          | ∅                              | Deprecated                                                                                                  |
| `podMonitor.additionalLabels`                          | ∅                              |                                                                                                             |
| `podMonitor.extraRelabelings`                          | `podMonitor.relabelings`       | The chart adds no default relabelings                                                                       |
| `podRollmeAnnotation` and`podValuesChecksumAnnotation` | ∅                              | Replaced by `rollWorkload`, enabled by default                                                              |
| `prometheusSink.*`                                     | ∅                              | Deprecated                                                                                                  |
| `psp.enabled`                                          | `psp.create`                   |                                                                                                             |
| `rbac.enabled`                                         | `rbac.create`                  |                                                                                                             |
| `secrets.generic`                                      | ⚠️                             | `secrets.generic` now takes raw values rather than base64 encoded values                                    |
| `sinks.*`                                              | ∅                              | Deprecated                                                                                                  |
| `sources.*`                                            | ∅                              | Deprecated                                                                                                  |
| `storage.mode`                                         | ∅                              | If `persistence.enabled` a PersistentVolumeClaim will be created, unless `persistence.existingClaim` is set |
| `storage.hostPath`                                     | ∅                              | Vector running as an Aggregator no longer supports `hostPath` based storage                                 |
| `storage.managedPersistentVolumeClaim.size`            | `persistence.size`             |                                                                                                             |
| `storage.managedPersistentVolumeClaim.storageClass`    | `persistence.storageClassName` |                                                                                                             |
| `storage.existingPersistentVolumeClaim`                | `persistence.existingClaim`    |                                                                                                             |
| `transforms.*`                                         | ∅                              | Deprecated                                                                                                  |
| `vectorApi.*`                                          | ∅                              | Deprecated                                                                                                  |

## HAProxy values

| Old parameter                      | New parameter  | Comment                                                       |
|------------------------------------|----------------|---------------------------------------------------------------|
| `config`                           | `customConfig` | Default HAProxy config can be overwritten with `customConfig` |
| `mountedSecrets`                   | ∅              |                                                               |
| `podSecurityContext.*`             | ⚠️             | `podSecurityContext` now takes an object                      |
| `replicaCount`                     | `replicas`     |                                                               |
| `service.clusterIP`                | ∅              |                                                               |
| `service.loadBalancerIP`           | ∅              |                                                               |
| `service.loadBalancerSourceRanges` | ∅              |                                                               |
