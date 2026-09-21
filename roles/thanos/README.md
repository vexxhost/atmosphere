# `thanos`

This role deploys Thanos Query, Query Frontend, Store Gateway, and Compactor
for long-term Prometheus metrics storage. The `kube_prometheus_stack` role
configures the matching Prometheus sidecar and object storage Secret.

Thanos is disabled by default. Set `thanos_enabled: true` and provide either
`thanos_object_storage_config` or
`thanos_object_storage_existing_secret` to enable it.
