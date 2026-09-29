# `nova`

## Configuration

`nova_helm_timeout` sets the maximum time allowed for Nova Helm operations. It
accepts a Go duration string such as `10m0s` and defaults to `5m0s`.

```yaml
nova_helm_timeout: 10m0s
```

## Bare metal graphical consoles

Nova can expose bare metal graphical consoles through its standard remote
console API and `nova-novncproxy`. Enable the Ironic compute service and its
VNC path with:

```yaml
nova_ironic_vnc_enabled: true
```

The Nova image used by `nova-compute-ironic` must implement the Ironic
driver's VNC console methods. The role configures the Ironic console-state
timeout and retains the unauthenticated RFB backend scheme required between
`nova-novncproxy` and the ephemeral console provider.

Set `nova_novnc_assets_image` to a digest-pinned image when different browser
assets are required. The image must provide `/usr/share/novnc`.
