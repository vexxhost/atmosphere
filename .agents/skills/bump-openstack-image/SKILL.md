---
name: bump-openstack-image
description: Bump an OpenStack service container image to the latest digest in `roles/defaults/vars/main.yml`, across one or more Atmosphere branches. Use this when asked to bump, refresh, or update the digest for a service image such as Magnum, Neutron, Nova, Cinder, Keystone, Glance, Heat, Manila, Barbican, Octavia, Placement, Horizon, Designate, Ironic, or similar.
---

# Bumping an OpenStack image to the latest digest

## Required inputs

Before starting, confirm the following inputs with the user:

1. **Service** (required) — the OpenStack service whose image should be
   bumped (for example `magnum`, `neutron`, `nova`). This maps one-to-one
   to a `ghcr.io/vexxhost/<service>` image and a
   `vexxhost/docker-<service>` source repository.
2. **Reason** (optional) — the fix, feature, or dependency update the
   bump is expected to bring in. When provided, it is used to validate
   that the expected change is actually present in the new image.
   Typical forms:
   - a commit SHA in `docker-<service>` or an upstream repo,
   - a PR number merged into `docker-<service>`,
   - a dependency version such as `magnum-cluster-api==0.36.5`.
3. **Stable branches** (optional) — the Atmosphere branches to update.
   If omitted, update every active branch: `main` plus every
   `stable/<release>` branch that still exists on `origin`.

If the user gives an ambiguous service name, resolve it by listing the
keys in `roles/defaults/vars/main.yml` under `_atmosphere_images:` that
start with `<service>_` and confirm which image repository is intended.

## Key conventions

The entries in `roles/defaults/vars/main.yml` look like:

    magnum_api: "{{ atmosphere_image_prefix }}ghcr.io/vexxhost/magnum:<tag>@sha256:<digest>"

The `<tag>` is tied to the Atmosphere branch, not chosen freely:

| Atmosphere branch | Image tag      | `docker-<service>` branch |
| ----------------- | -------------- | ------------------------- |
| `main`            | `main`         | `main`                    |
| `stable/2025.2`   | `2025.2`       | `stable/2025.2`           |
| `stable/2025.1`   | `2025.1`       | `stable/2025.1`           |
| `stable/2024.2`   | `2024.2`       | `stable/2024.2`           |
| `stable/<rel>`    | `<rel>`        | `stable/<rel>`            |

Always keep the tag as-is and only replace the `@sha256:...` suffix.
Never rewrite a tag to point at a different branch's image.

A single service usually appears in several variable names that all
share the same image (for example `magnum_api`, `magnum_conductor`,
`magnum_db_sync`, `magnum_cluster_api_proxy`). Bump every entry that
points at `ghcr.io/vexxhost/<service>:<tag>@sha256:...` with the same
new digest. Leave unrelated images on different repositories
(for example `magnum_registry` which points at
`quay.io/vexxhost/magnum-cluster-api-registry`) untouched.

## Workflow

Perform the following for each requested Atmosphere branch. Do one
branch per pull request; do not mix branches in a single PR.

### 1. Pick the set of branches

- If the user gave an explicit list, use it.
- Otherwise, enumerate branches with
  `git ls-remote --heads origin 'stable/*'` and include `main`.
- Validate every requested branch exists on `origin`. Stop and ask if
  one does not.

### 2. Check out the Atmosphere branch

Use the branch the bump targets as your working branch base. For every
branch other than the current one, create a new working branch from
`origin/<branch>` (for example `bump-<service>-<branch>`).

### 3. Identify the current image reference

Read `roles/defaults/vars/main.yml` and collect every line that matches
`ghcr.io/vexxhost/<service>:<tag>@sha256:<digest>`. Record:

- the image tag (must match the branch convention above — flag a
  mismatch and stop if it does not),
- the existing digest.

### 4. Resolve the latest digest for that tag

Query the GitHub Container Registry for the current digest of
`ghcr.io/vexxhost/<service>:<tag>`. Any of the following is fine, in
order of preference:

1. `crane digest ghcr.io/vexxhost/<service>:<tag>`
2. `skopeo inspect docker://ghcr.io/vexxhost/<service>:<tag>`
   and read the `Digest` field
3. A direct HTTPS call to the registry:

   - `GET https://ghcr.io/token?scope=repository:vexxhost/<service>:pull`
     to obtain an anonymous bearer token
   - `GET https://ghcr.io/v2/vexxhost/<service>/manifests/<tag>`
     with `Accept: application/vnd.oci.image.index.v1+json,
     application/vnd.docker.distribution.manifest.list.v2+json,
     application/vnd.oci.image.manifest.v1+json,
     application/vnd.docker.distribution.manifest.v2+json`. Read the
     digest from the `Docker-Content-Digest` response header.

If the resolved digest equals the digest already in the file, the bump
is a no-op. Stop and report this to the user before making any change.

### 5. Look up the image's source commit

The `org.opencontainers.image.revision` annotation on the manifest
records the `docker-<service>` commit the image was built from. Fetch
the full manifest (not just the digest):

    GET https://ghcr.io/v2/vexxhost/<service>/manifests/<digest>

For a manifest list / OCI image index, pick any single-platform
manifest inside it and fetch that; the annotations are identical
across platforms for these builds. Equivalently, `crane manifest` or
`skopeo inspect --raw` returns the same JSON.

Extract:

- `annotations["org.opencontainers.image.revision"]` — the source SHA.
- `annotations["org.opencontainers.image.source"]` — sanity-check that
  it points at `https://github.com/vexxhost/docker-<service>`.

### 6. Verify the source SHA is on the matching `docker-<service>` branch

Using the GitHub API (no clone needed):

    GET https://api.github.com/repos/vexxhost/docker-<service>/branches/<docker-branch>

where `<docker-branch>` is the branch matching the Atmosphere branch
per the conventions table (`main` ↔ `main`, `stable/<rel>` ↔
`stable/<rel>`).

The source SHA from step 5 **must** match `commit.sha` on that branch.
If it does not, the registry tag is stale — a build has not yet run
for the latest commit, or the tag is pointing at the wrong branch. In
that case, stop and report the mismatch. Do not bump to a stale image.

If the SHAs match, the image is the latest build of the correct
branch and is safe to pin.

### 7. If a reason was provided, validate the fix is present

Use the reason to confirm the new image actually contains the intended
change. Choose the check that fits the reason:

- **Commit SHA or PR in `docker-<service>`**: confirm it is an ancestor
  of the source SHA from step 5. The GitHub compare API works well:

      GET https://api.github.com/repos/vexxhost/docker-<service>/compare/<source-sha>...<fix-sha>

  The fix SHA is included when `status` is `identical` or `behind`.

- **Dependency version** (for example `magnum-cluster-api==0.36.5`):
  read the relevant file on the `docker-<service>` branch at the source
  SHA — typically `requirements.txt`, `pyproject.toml`,
  `upper-constraints.txt`, or similar — and confirm the pinned version
  matches.

  This can be done with:

      GET https://api.github.com/repos/vexxhost/docker-<service>/contents/<path>?ref=<source-sha>

- **Upstream OpenStack fix**: identify which requirement pulls the fix
  in, then apply the dependency-version check above.

If the validation fails, stop and tell the user which expectation was
not met. Do not open a PR that does not deliver the stated fix.

### 8. Update `roles/defaults/vars/main.yml`

Replace the `@sha256:<old-digest>` suffix with `@sha256:<new-digest>`
on every line for the service (see step 3). Keep the tag and image
path unchanged. Make no other edits to the file.

### 9. Add a release note

Generate a release note with `reno`:

    reno new bump-<service>-<short-slug>

Use the `fixes` category when a reason was provided, otherwise use
`upgrade`. Keep the note brief, in natural English, and written from
the project's perspective. Wrap technical terms in RST double
backticks. The note must pass `vale`. Examples:

    ---
    fixes:
      - |
        The Magnum container image now includes the Cluster API
        driver for Magnum version 0.36.5.

    ---
    upgrade:
      - |
        The Neutron container image now includes the latest
        upstream fixes.

### 10. Commit and open the pull request

Commit with a Conventional Commits message and a DCO sign-off. Use
`fix` when a reason was given, otherwise `chore`:

    fix(<service>): bump <service> image to <short description>
    chore(<service>): bump <service> image digest

Open one pull request per branch with `base` set to the matching
Atmosphere branch (for example `stable/2025.1`, or `main`). The PR
title must also follow Conventional Commits, since it becomes the
squash-merge commit message.

Include in the PR body:

- the service and target branch,
- the old and new digests,
- the source SHA from the image annotation and a link to the
  `docker-<service>` commit,
- the reason (when provided) and how it was validated.

## Common pitfalls

- **Tag/branch mismatch**: never bump a `stable/<rel>` branch using the
  digest of the `:main` tag, and vice versa. The tag in the file must
  match the Atmosphere branch being updated.
- **Stale tag**: a newer commit may exist on `docker-<service>` that
  has not yet been published. The step 6 check catches this — do not
  work around it by bumping to an older digest or by pushing the
  docker repo.
- **Multi-arch manifests**: the top-level manifest for a tag is often
  an OCI image index. `org.opencontainers.image.revision` is present
  on each per-platform manifest; fetch one of them to read it.
- **Partial updates**: a service typically has several entries
  (`*_api`, `*_conductor`, `*_db_sync`, and others) that share the
  same image. Update them together so the file stays consistent.
- **Unrelated images**: services sometimes reference auxiliary images
  from other repositories (for example a registry sidecar). Those are
  out of scope for a digest bump of the service image itself.
- **No-op bumps**: if the registry digest already matches what is in
  the file, stop and tell the user rather than opening an empty PR.
