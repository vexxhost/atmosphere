# `keycloak`

## Configuration

`keycloak_helm_timeout` sets the maximum time allowed for Keycloak Helm
operations. It accepts a Go duration string such as `15m0s` and defaults to
`10m0s`.

```yaml
keycloak_helm_timeout: 15m0s
```

Keycloak database connections enable causal reads with the MySQL session
variable `wsrep_sync_wait=1`. Reads wait for pending Galera replication events
to be applied, avoiding stale reads when a connection moves to another database
node after failover. This setting applies only to Keycloak connections and does
not change the database defaults for other services. Reads can take longer while
the database node catches up with replication.
