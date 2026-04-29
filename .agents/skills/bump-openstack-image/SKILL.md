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
   that the expected change is actually present in the new image, and to
   write a meaningful release note. Typical forms:
   - a commit SHA in `docker-<service>` or an upstream repo,
   - a PR number merged into `docker-<service>`,
   - a dependency version such as `magnum-cluster-api==0.36.5`,
   - a release URL such as `https://github.com/vexxhost/magnum-cluster-api/releases/tag/v0.36.5`.
3. **Stable branches** (optional) — the Atmosphere branches to update.
   If omitted, update every active branch: `main` plus every
   `stable/<release>` branch that still exists on `origin`.

If the user gives an ambiguous service name, resolve it by listing the
keys in `roles/defaults/vars/main.yml` under `_atmosphere_images:` that
start with `<service>_` and confirm which image repository is intended.

## Key conventions

The entries in `roles/defaults/vars/main.yml` look like:

    magnum_api: "{{ atmosphere_image_prefix }}ghcr.io/vexxhost/magnum:<tag>@sha256:<digest>"

The `<tag>` is tied to the Atmosphere branch. For `main` the tag is
`main`; for `stable/<rel>` branches the tag is `<rel>` (the release
name without the `stable/` prefix). Always keep the tag as-is and only
replace the `@sha256:...` suffix. Never rewrite a tag to point at a
different branch's image.

The image's `org.opencontainers.image.version` label (read via
`crane config`) records this tag and is the authoritative way to
confirm which branch an image belongs to. To recover the
`docker-<service>` branch from it, prepend `stable/` when the value is
not `main` (for example `version=2025.1` → branch `stable/2025.1`).

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
  `git ls-remote --heads origin 'refs/heads/stable/*'` and include `main`.
- Validate every requested branch exists on `origin`. Stop and ask if
  one does not.

### 2. Stash any uncommitted work

Before creating any branches, stash uncommitted changes so they don't
interfere:

    git stash

### 3. Identify the current image reference on `main`

Read `roles/defaults/vars/main.yml` on `main` and collect every line
that matches `ghcr.io/vexxhost/<service>:<tag>@sha256:<digest>`. Pick
one representative image reference (any entry sharing the same digest
is fine).

### 4. Confirm the source repository from the current image

Run `crane config` on the representative reference from step 3 to
confirm the source repository:

    crane config "$IMAGE" | jq '.config.Labels'

Record:

- **`org.opencontainers.image.source`** — the source repository URL
  (for example `https://github.com/vexxhost/docker-magnum` →
  `vexxhost/docker-magnum`). This is the authoritative source of truth;
  do not guess it from the service name alone.
- **`org.opencontainers.image.version`** — must match the tag in the
  image reference. Flag a mismatch and stop if it does not.

You only need to do this once (on `main`). The source repository is the
same across all branches for the same service.

### 5. Resolve and validate new digests for all branches in parallel

Before touching git at all, resolve and validate every branch at once.
For each branch tag (`main`, `zed`, `2025.1`, etc.):

a. Read the old digest from the file on that branch:

    git show origin/<branch>:roles/defaults/vars/main.yml | grep "ghcr.io/vexxhost/<service>:<tag>@"

b. Fetch the latest digest:

    crane digest ghcr.io/vexxhost/<service>:<tag>

   If the new digest equals the old digest, that branch is a no-op —
   skip it and report this to the user.

c. Inspect the new image labels:

    crane config "ghcr.io/vexxhost/<service>:<tag>@<new-digest>" | jq '.config.Labels'

   Verify `org.opencontainers.image.version` matches the expected tag
   and record `org.opencontainers.image.revision` (the new source SHA).

d. Confirm the new source SHA matches the HEAD of the corresponding
   `docker-<service>` branch (derived from the version label: prepend
   `stable/` when the value is not `main`):

    gh api repos/vexxhost/docker-<service>/branches/<docker-branch> --jq '.commit.sha'

   The SHA must match. If it does not, the registry tag is stale — stop
   and report the mismatch. Do not bump to a stale image.

Batch these calls as much as possible. All branches can be checked in a
single loop before any git operations begin.

### 6. If a reason was provided, validate the fix is present

Use the reason to confirm the new image actually contains the intended
change. Do this check once against the `main` source SHA — if it passes
on `main`, check each stable branch's source SHA too (they may have
different dependency versions). Choose the check that fits the reason:

- **Commit SHA or PR in `docker-<service>`**: confirm it is an ancestor
  of the source SHA from step 5c. Use the GitHub compare API:

      gh api repos/vexxhost/docker-<service>/compare/<new-source-sha>...<fix-sha>

  The fix SHA is included when `status` is `identical` or `behind`.

- **Dependency version** (for example `magnum-cluster-api==0.36.5`):
  read the relevant file on the `docker-<service>` branch at the source
  SHA — typically `Dockerfile`, `requirements.txt`, `pyproject.toml`,
  `upper-constraints.txt`, or similar — and confirm the pinned version
  matches:

      gh api repos/vexxhost/docker-<service>/contents/<path>?ref=<new-source-sha> --jq '.content' | base64 -d | grep <dependency>

- **Upstream OpenStack fix**: identify which requirement pulls the fix
  in, then apply the dependency-version check above.

If the validation fails for any branch, stop and tell the user which
expectation was not met. Do not open PRs for branches that do not
deliver the stated fix.

### 7. Write the release note (once, on `main`)

If a reason was given, look at the upstream release or changelog to
understand what actually changed. For a dependency version bump, fetch
the GitHub release notes or compare the diff between the old and new
versions:

    gh api repos/<upstream-owner>/<upstream-repo>/releases/tags/<new-tag> --jq '.body'
    gh api repos/<upstream-owner>/<upstream-repo>/compare/<old-tag>...<new-tag> --jq '.commits[].commit.message'

Use these to write a specific, concise release note — not vague phrases
like "several key fixes". Summarize the actual changes in one or two
sentences.

Generate the note on `main`:

    reno new bump-<service>-<short-slug>

Use the `fixes` category when a reason was provided, otherwise use
`upgrade`. Write in natural English from the project's perspective.
Avoid using the raw package name (for example write "the Cluster API
driver for Magnum" instead of "magnum-cluster-api"). Wrap technical
terms such as config option names in RST double backticks. Run `vale`
before committing:

    vale releasenotes/notes/<note-file>.yaml

Example:

    ---
    fixes:
      - |
        The Magnum container image now includes the Cluster API driver
        for Magnum version 0.36.6, which preserves
        ``disableAPIServerFloatingIP`` during cluster upgrades and fixes
        file descriptor leaks in the Rust components.

### 8. Apply changes and open pull requests

For each branch that has a new digest (skipping no-op branches):

a. **Create a working branch** from `origin/<branch>`. Use the release
   name without the `stable/` prefix in the branch name to avoid
   slashes (for example `bump-magnum-2025.1`, `bump-magnum-main`):

       git checkout -b bump-<service>-<tag> origin/<branch>

b. **Update `roles/defaults/vars/main.yml`**: replace
   `@sha256:<old-digest>` with `@sha256:<new-digest>` on every line for
   the service. Keep the tag and image path unchanged. Make no other
   edits.

c. **Add the release note**:
   - For `main`: the note was already generated in step 7. Stage it.
   - For stable branches: copy the exact same reno file from `main`
     (same filename including the hash) rather than running `reno new`
     again. This is how reno tracks the same note across branches.

       git show bump-<service>-main:releasenotes/notes/<note-file>.yaml > releasenotes/notes/<note-file>.yaml

d. **Commit** with a Conventional Commits message and a DCO sign-off.
   Use `fix` when a reason was given, otherwise `chore`:

       git commit -s -m "fix(<service>): bump <service> image to <short description>"

e. **Push and open a pull request** targeting the matching Atmosphere
   branch. Always pass `--repo vexxhost/atmosphere` explicitly to avoid
   issues with unset defaults. The PR title must follow Conventional
   Commits and **include the target branch in parentheses** so that
   multiple backport PRs are distinguishable in the PR list:

       gh pr create \
         --repo vexxhost/atmosphere \
         --base <branch> \
         --title "fix(<service>): <description> (<branch>)" \
         --body "..."

   Include in the PR body:
   - the service and target branch,
   - the old and new digests,
   - the old and new source SHAs with links to the `docker-<service>`
     commits,
   - the reason (when provided) and how it was validated.

## Common pitfalls

- **Tag/branch mismatch**: never bump a `stable/<rel>` branch using the
  digest of the `:main` tag, and vice versa. The `version` label from
  step 4 must match the tag in the image reference in the file.
- **Stale tag**: a newer commit may exist on `docker-<service>` that
  has not yet been published. The step 5d check catches this — do not
  work around it by bumping to an older digest or by pushing the
  docker repo.
- **Partial updates**: a service typically has several entries
  (`*_api`, `*_conductor`, `*_db_sync`, and others) that share the
  same image. Update them together so the file stays consistent.
- **Unrelated images**: services sometimes reference auxiliary images
  from other repositories (for example a registry sidecar). Those are
  out of scope for a digest bump of the service image itself. Use the
  `source` label from step 4 to confirm you are working with the right
  repository before making any changes.
- **No-op bumps**: if the registry digest already matches what is in
  the file, skip that branch and tell the user rather than opening an
  empty PR.
- **Ambiguous PR list**: when opening multiple backport PRs with the
  same fix, the titles will be identical and impossible to tell apart in
  the GitHub PR list. Always include the target branch in the PR title
  (for example `(stable/2025.1)` or `(main)`).
- **Working branch names with slashes**: `stable/2025.1` cannot be used
  in a git branch name. Strip the `stable/` prefix:
  `bump-<service>-2025.1`, not `bump-<service>-stable/2025.1`.
- **Unset default repo**: `gh pr create` without `--repo` fails if no
  default repository is configured. Always pass
  `--repo vexxhost/atmosphere` explicitly.
- **Vague release notes**: do not write generic phrases like "several
  key fixes". Fetch the upstream release notes or commit diff and
  summarize the actual changes.
- **Release notes on stable branches**: do not run `reno new` on stable
  branches. Copy the exact same reno file (same filename with hash)
  from `main`. This is how reno tracks the same note across branches.
