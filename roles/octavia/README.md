# `octavia`

## Configuration

`octavia_helm_timeout` sets the maximum time allowed for Octavia Helm
operations. It accepts a Go duration string such as `10m0s` and defaults to
`5m0s`.

```yaml
octavia_helm_timeout: 10m0s
```

The role uses the containerized OpenStack CLI to ensure unlimited instance,
core, RAM, volume, volume capacity, security group, and security group rule
quotas for the `admin` project. It updates quotas only when needed and verifies
the result. Check mode reports pending changes without updating quotas.
