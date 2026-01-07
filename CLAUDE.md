# Atmosphere Project Guidelines

## Commits

Use conventional commits: `type(scope): message`

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`

## Release Notes

- Use `reno new <slug>` to generate a new release note
- Keep notes brief and concise - detailed usage belongs in documentation
- Categories: `features`, `issues`, `upgrade`, `deprecations`, `critical`, `security`, `fixes`, `other`
- Avoid variable names or code examples
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

## Vale Vocabulary

For `.github/styles/config/vocabularies/Base/accept.txt`:

- Only add words/terms, not variable names
- Capitalize proper nouns (e.g., `Neutron` not `neutron`)
