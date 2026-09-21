# `ironic`

The Ironic role deploys the OpenStack Bare Metal service. It is available from
the standard `playbooks/openstack.yml` workflow but remains disabled by
default.

Enable it in inventory variables:

```yaml
atmosphere_ironic_enabled: true
```

The playbook condition uses `default(false)`, so inventories that do not define
the variable retain the existing deployment behavior.
