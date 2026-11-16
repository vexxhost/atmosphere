# `keycloak`

## Configuration

`keycloak_helm_timeout` sets the maximum time allowed for Keycloak Helm
operations. It accepts a Go duration string such as `15m0s` and defaults to
`10m0s`.

```yaml
keycloak_helm_timeout: 15m0s
```
