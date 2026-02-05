---
applyTo: "roles/defaults/vars/main.yml"
---

# Docker image digest review (ghcr.io/vexxhost)

## Scope
These instructions are for Renovate PRs titled **"vexxhost images"** that bump digests for images hosted under ``ghcr.io/vexxhost/*``. They focus on validating the provenance and change trail for each updated image digest and summarizing the root change.

## Prerequisites
- ``skopeo``
- ``git`` (``gh`` optional)

## Process (per image)
This is a **recursive** process. At each level, apply the same steps until you reach the root change.

1. Pull old/new digests from the PR diff.
2. Inspect each digest:
   ```bash
   skopeo inspect docker://ghcr.io/vexxhost/<image>:<tag>@sha256:<digest>
   ```
   If labels are missing, retry with ``skopeo inspect --config``.
3. Capture label values:
   - ``org.opencontainers.image.source`` (repo URL)
   - ``org.opencontainers.image.revision`` (commit SHA)
4. Diff old vs new revisions in the source repo:
   - ``git log --oneline <old>..<new>``
   - Or use GitHub API: ``gh api repos/{owner}/{repo}/compare/{old}...{new}``
5. For each commit in that diff, check what changed:
   - **Base image digest bump** → repeat this process for that image.
   - **Upstream software ref bump** (e.g., Glance, Cinder) → clone the upstream repo and diff the old/new refs.
   - **Package version bump** (PyPI, etc.) → note the version change.
   - **Config/build change** → note directly.
6. Continue recursively until you reach the root cause (e.g., an upstream OpenStack commit, a PyPI release, or a base OS image update).
7. Summarize in the review:
   - Old → new digest
   - Chain of repos/revisions traced
   - Shortdiff with commit links at each level
   - Root cause and notable changes

## Review workflow
**Trace all images first, then leave one comment.** Many images often share the same root cause (e.g., a base image bump). By tracing all images before commenting, you can consolidate findings into a single review comment rather than repeating the same information for each image.

## Example walkthrough (PR #3534)
Digest bump:
- ``ghcr.io/vexxhost/cinder:2023.2`` old → new

**Level 1**: Inspect both digests, get labels pointing to ``docker-cinder`` repo. Diff the revisions.

**Level 2**: If docker-cinder commit bumps a base image digest (e.g., ``openstack-venv-builder``), inspect that image's old/new digests and diff its source repo.

**Level 3**: If that repo bumps the Cinder upstream ref, clone ``https://opendev.org/openstack/cinder`` and diff the old/new refs.

Continue until you find the root change. Include shortdiff + commit links for each level in the review.

## Extending later
If new registries or image families are added, mirror the process above in a new section.
