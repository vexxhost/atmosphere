# `nova`

## Configuration

`nova_helm_timeout` sets the maximum time allowed for Nova Helm operations. It
accepts a Go duration string such as `10m0s` and defaults to `5m0s`.

```yaml
nova_helm_timeout: 10m0s
```

## Bare metal graphical consoles

Nova serves bare metal graphical consoles through its standard remote console
API and `nova-novncproxy` once Ironic graphical consoles are enabled and
`nova-compute-ironic` is running. The Ironic compute service is not deployed by
default; enable it with:

```yaml
nova_helm_values:
  manifests:
    statefulset_compute_ironic: true
```

The Nova image must include the Ironic driver's VNC console support (Nova
2026.1 or later). Nova's `[vnc] auth_schemes` is already `vencrypt,none`, which
lets the proxy reach the console provider without authentication while
libvirt hosts keep using VeNCrypt. Nova's `[ironic] vnc_console_state_timeout`
defaults to 60 seconds and can be tuned through `nova_helm_values` under
`conf.nova_ironic`.
