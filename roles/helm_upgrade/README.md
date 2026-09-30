# `helm_upgrade`

This role ensures smooth Helm upgrades by handling immutable field
changes and maintaining high availability (HA).

## Key Features

- Helm Release Check: Confirms if the release exists.
- Immutable Field Change Detection: Detects changes in specified immutable fields.
- Orphan Resource Deletion: Deletes affected resources while preserving child resources.
- Helm Upgrade: Performs the upgrade after resolving immutable field conflicts.
