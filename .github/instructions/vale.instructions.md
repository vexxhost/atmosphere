---
applyTo: "doc/**,releasenotes/**,.github/styles/config/vocabularies/Base/accept.txt"
---

All documentation and release notes must pass `vale` linting with zero
errors, zero warnings, and zero suggestions.  Run `vale` before
committing:

    vale <file>

## Vale configuration

The project uses the Microsoft style guide with a custom vocabulary.
Configuration is in `.vale.ini` at the repository root.  The minimum
alert level is `suggestion`, meaning all suggestions are treated as
failures.

**Note:** Vale linting only applies to files matching the patterns in
`.vale.ini` (currently `*.{rst,yaml}`).  Files in `.github/instructions/`
are markdown files and are not subject to Vale linting.

## Common rules to follow

- Use single spaces between sentences, not double spaces.
- Use contractions (e.g., "it's" instead of "it is", "don't" instead
  of "do not").
- Avoid passive voice (e.g., "the alert fires" instead of "the alert
  is fired").
- Use sentence-style capitalization for headings (only capitalize the
  first word and proper nouns).
- Avoid first-person plural ("we", "our").  Write from the project's
  perspective instead.
- Use "for example" instead of "e.g.,".
- Avoid unnecessary adverbs like "naturally", "effectively", "very".
- Use the Oxford comma.
- Keep sentences under 30 words when possible.
- Spell out acronyms on first use unless they are in the vocabulary.

## Vocabulary

The vocabulary file is at
`.github/styles/config/vocabularies/Base/accept.txt`.

When adding words to the vocabulary:

- Only add proper nouns and domain-specific terms, not variable names
  or command names.
- Use RST backticks (double backticks in RST files) for technical
  terms, paths, and command names instead of adding them to the
  vocabulary.
- Capitalize proper nouns (e.g., `Neutron` not `neutron`).
- Entries must be sorted in lexicographic (byte) order.  The
  `file-contents-sorter` pre-commit hook enforces this automatically.
  In byte order, all uppercase letters sort before all lowercase
  letters (e.g., `Z` before `a`), and within the same case, entries
  sort alphabetically (e.g., `Galera` before `Glance`).

## Release notes

Release notes are YAML files in `releasenotes/notes/`.  They must also
pass `vale` linting.  Write release notes in natural English, not
technical jargon (e.g., "DHCP client" not "dhclient").
