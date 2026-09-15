# `ironic`

## Bare metal graphical consoles

Graphical console support is disabled by default. Enable it and provide an
immutable console backend image that implements Ironic's `APP`, `APP_INFO`, and
`READ_ONLY` environment contract and listens for RFB connections on port 5900:

```yaml
ironic_vnc_enabled: true
ironic_vnc_namespace: openstack-ironic-vnc
atmosphere_image_overrides:
  ironic_console: registry.example.com/ironic-console@sha256:<digest>
```

The `ironic_console` entry is optional while graphical consoles are disabled.
When enabled, the role requires a digest-pinned override and passes it to
Ironic as the dynamic console backend image.

The namespace defaults to
`{{ ironic_helm_release_namespace }}-ironic-vnc`; for the standard `openstack`
release this is `openstack-ironic-vnc`. The role creates the namespace and
enables its RFB NetworkPolicy by default. The Ironic API and noVNC endpoint
hosts must be distinct. Disabling the feature fails while dynamic console Pods
or Secrets remain, and removes the role-owned noVNC Ingress only after that
preflight succeeds.

The role deploys `ironic-novncproxy`, configures the Kubernetes console
container provider, and enables both `redfish-graphical` and `no-console`.
Select `redfish-graphical` only on nodes supported by the chosen backend image.
By default, noVNC browser assets come from Atmosphere's standard Nova image.
Set `atmosphere_image_overrides.ironic_novncproxy_assets` to a digest-pinned
image when different browser assets are required. The replacement image must
provide `/usr/share/novnc`; the chart copies these files without rewriting
JavaScript.
