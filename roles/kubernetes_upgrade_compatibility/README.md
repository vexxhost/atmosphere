# Kubernetes upgrade compatibility

This role protects application discovery while controller API and DNS endpoints
change. The Kubernetes playbook configures it through the collection's upgrade
lifecycle hooks; it runs around controller operations rather than as a separate
deployment step.

## Behavior

- Prepare the existing Cilium release with the compatibility settings, preserving
  explicit values and operator environment entries by name.
- Temporarily suppress NFD publication and pause Percona peer discovery while
  preserving existing labels, process identities and established sessions.
- Restore owned state after success or failure. Host watchdogs retry recovery if
  the deployer disconnects, and identity checks avoid overwriting concurrent
  changes.

Controller placement, the NFD namespace and the operation timeout reuse existing
deployment settings. Worker-only recovery skips controller preparation. This
role does not perform runtime or etcd intermediate upgrades or replace external
service acceptance checks.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `atmosphere_kubernetes_upgrade_compatibility` | `true` | Enable the compatibility profile and lifecycle integration. |
| `atmosphere_kubernetes_upgrade_nfd_configmap` | `node-feature-discovery-worker-conf` | Identify the NFD worker configuration when using a custom Helm fullname. |
| `atmosphere_kubernetes_upgrade_nfd_pod_prefix` | `node-feature-discovery-worker-` | Identify the corresponding NFD worker pods. |

Keep compatibility enabled for the affected bundled clients. Disable it only
when separately delivered application and Cilium fixes replace the profile.
Other application versions and placements require their own qualification.

The companion Kubernetes collection must provide the controller lifecycle hooks
and Cilium values filter. See the [upgrade guide](../../doc/source/admin/upgrading.rst)
for prerequisites, version-specific protections and validation boundaries.
