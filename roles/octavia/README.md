# `octavia`

## Configuration

`octavia_helm_timeout` sets the maximum time allowed for Octavia Helm
operations. It accepts a Go duration string such as `10m0s` and defaults to
`5m0s`.

```yaml
octavia_helm_timeout: 10m0s
```
