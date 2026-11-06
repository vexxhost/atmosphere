# `nova`

## Configuration

`nova_helm_timeout` sets the maximum time allowed for Nova Helm operations. It
accepts a Go duration string such as `10m0s` and defaults to `5m0s`.

```yaml
nova_helm_timeout: 10m0s
```

## Sunrise noVNC console

The Nova chart deploys the Sunrise console assets alongside the upstream noVNC
client. It preserves `vnc.html` and `vnc_lite.html` while adding
`sunrise.html`, `sunrise.css`, and `sunrise.js`. Updating these assets
automatically rolls the `nova-novncproxy` deployment.

The noVNC image must provide `/usr/share/novnc/core/rfb.js`. The ingress must
allow the Sunrise dashboard origin to frame the console and must not send
`X-Frame-Options: DENY`.
