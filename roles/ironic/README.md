# `ironic`

## Bare metal graphical consoles

Graphical console support is disabled by default. Enable it and provide an
immutable console backend image that implements Ironic's `APP`, `APP_INFO`, and
`READ_ONLY` environment contract and listens for RFB connections on port 5900:

```yaml
ironic_vnc_enabled: true
atmosphere_image_overrides:
  ironic_console: registry.example.com/ironic-console@sha256:<digest>
```

The `ironic_console` entry is optional while graphical consoles are disabled.
When enabled, the role requires a digest-pinned override and passes it to
Ironic as the dynamic console backend image.

The role deploys `ironic-novncproxy`, configures the Kubernetes console
container provider, and enables both `redfish-graphical` and `no-console`.
Select `redfish-graphical` only on nodes supported by the chosen backend image.
By default, noVNC browser assets come from Atmosphere's standard Nova image.
Set `atmosphere_image_overrides.ironic_novncproxy_assets` to a digest-pinned
image when different browser assets are required. The replacement image must
provide `/usr/share/novnc`; the chart copies these files without rewriting
JavaScript.

### BMC TLS trust

Console backends can trust a private BMC certificate authority from a
Kubernetes Secret in the Ironic release namespace. The Secret is validated
before the Helm release is changed, mounted read-only in each dynamic console
Pod, and exposed to the backend through `BMC_CA_FILE`:

```yaml
ironic_vnc_ca_secret_name: bmc-ca
ironic_vnc_ca_secret_key: ca.crt
```

The backend image must consume the `BMC_CA_FILE`,
`BMC_TLS_MINIMUM_VERSION`, and optional `BMC_TLS_CIPHERS` environment
variables. TLS 1.2 is the default minimum. To set an explicit cipher policy:

```yaml
ironic_vnc_tls_minimum_version: "1.3"
ironic_vnc_tls_ciphers: TLS_AES_256_GCM_SHA384
```

Certificate verification can be disabled explicitly when the selected backend
supports that policy:

```yaml
ironic_vnc_allow_insecure_tls: true
```
