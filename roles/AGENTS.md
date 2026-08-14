# roles/AGENTS.md

## Review guidelines

Apply these rules both when making changes and when reviewing PRs that change
Cluster API, kubeadm bootstrap/control-plane, `clusterctl`, or CAPO/OpenStack
provider versions under `roles/`:

- Keep Atmosphere defaults and Magnum dependencies in sync:
  `clusterctl_version` and `cluster_api_version` in
  `roles/magnum/meta/main.yml` must match the core Cluster API image tags in
  `roles/defaults/vars/main.yml`, and `cluster_api_infrastructure_version` must
  match the CAPO image tag.
- Check `vexxhost/ansible-collection-kubernetes` for the exact target versions
  before treating the Atmosphere change as ready.
- If support is missing, open a companion collection PR and link it from the
  Atmosphere PR description or comments.
- Do not treat the Atmosphere change as complete until support is verified or
  the linked companion PR exists.
