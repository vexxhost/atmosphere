---
applyTo: "charts/**/values.yaml,roles/defaults/vars/main.yml"
---

# Helm Chart Guidelines

This document contains guidelines for working with Helm charts in the
Atmosphere project.

## Image Pinning Convention

**Chart values in `charts/` directories do NOT need image digest pins.**

Image pinning with sha256 digests is done exclusively in
`roles/defaults/vars/main.yml`. The Helm chart values files use mutable
tags (e.g., `v1.0.1`) without digests, and these are overridden at
deployment time by the pinned values from the Ansible roles.

### Examples

**Incorrect approach** (do not pin in chart values):
```yaml
# charts/libvirt/values.yaml - NO digest pins
images:
  tags:
    libvirt_tls_sidecar: ghcr.io/vexxhost/libvirt-tls-sidecar:v1.0.1@sha256:669f92c09a7d80667440d850bdce81ae67a57d3f473b21d2382d434512093d53
```

**Correct approach**:
```yaml
# charts/libvirt/values.yaml - Use tag without digest
images:
  tags:
    libvirt_tls_sidecar: ghcr.io/vexxhost/libvirt-tls-sidecar:v1.0.1

# roles/defaults/vars/main.yml - Pin with digest here
libvirt_tls_sidecar: "{{ atmosphere_image_prefix }}ghcr.io/vexxhost/libvirt-tls-sidecar:v1.0.1@sha256:669f92c09a7d80667440d850bdce81ae67a57d3f473b21d2382d434512093d53"
```

### Rationale

- Centralized image management in Ansible roles simplifies version
  updates and security audits
- Chart values remain clean and readable without lengthy digest strings
- Ansible deployment overrides chart defaults with pinned versions
- Reduces duplication and potential inconsistency between chart values
  and role defaults

### When Reviewing Changes

When reviewing pull requests that modify Helm chart values:

- Do NOT request adding sha256 digests to image references in
  `charts/**/values.yaml` files
- DO verify that corresponding entries in `roles/defaults/vars/main.yml`
  have proper sha256 digest pins when images are updated
- DO ensure image tags in chart values match the unpinned portion of the
  pinned image reference in the role defaults
