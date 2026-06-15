# Atmosphere Project Guidelines

## Commits

Use conventional commits: `type(scope): message`

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`

All commits must have a DCO sign-off (`-s` flag).

## Pull Requests

PR titles should follow conventional commits format (used for squash merge commit).

## Release Notes

- Use `reno new <slug>` to generate a new release note
- Keep notes brief and concise - detailed usage belongs in documentation
- Categories: `features`, `issues`, `upgrade`, `deprecations`, `critical`, `security`, `fixes`, `other`
- Write natural English, not technical jargon (e.g., "DHCP client" not "dhclient")
- Wrap paths and technical terms in RST backticks (e.g., ``/etc/resolv.conf``)
- Write from the project's perspective (e.g., "The default images..." not "Atmosphere default images...")
- Must pass `vale` linting

## Ansible Role Defaults

Brief description, blank line, then commented example, then default value:

```yaml
# Brief description of what this does.
#
# my_var:
#   - name: example
#     key: value
my_var: []
```

## Documentation

Always update documentation when adding features or improvements.

## Helm Charts

The setup ensures reproducible, auditable chart modifications:

1. Upstream charts are defined in `.charts.yml` (source of truth for versions)
2. Patches in `charts/patches/` track all customizations as discrete, reviewable changes
3. `charts/` contains the final result (upstream + patches applied)

Why this matters:

- When upstream releases a new version, update `.charts.yml` and re-run `chart-vendor`. It fetches the new upstream and re-applies patches
- If patches don't apply cleanly to the new upstream, you know immediately what broke
- All customizations are visible as patches rather than hidden in a large vendored directory
- CI verifies that `charts/` = upstream + patches (no drift)

To modify a chart: edit `charts/` and add corresponding patch to `charts/patches/`.
