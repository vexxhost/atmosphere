# `manila`

## Configuration

`manila_helm_timeout` sets the maximum time allowed for Manila Helm operations.
It accepts a Go duration string such as `10m0s` and defaults to `5m0s`.

```yaml
manila_helm_timeout: 10m0s
```

When the default Glance image backend is Cinder, Atmosphere converts and
uploads the Manila service image as `raw`. Other image backends keep the
`qcow2` default. Set `manila_image_disk_format` only when a custom Glance
configuration requires a different target format.
