# `multipath-tools` for Linux

This role owns `/etc/multipath.conf`, installs the multipath package, and
reloads `multipathd` when its configuration changes.

List every array used by a host in `multipathd_arrays`, in inventory shared by
all playbooks. For example, controllers and computes can have different lists:

```yaml
# group_vars/controllers.yml
multipathd_arrays: [netapp_ontap]
```

```yaml
# group_vars/computes.yml
multipathd_arrays: [netapp_ontap, pure_flasharray]
```

A nonempty list enables device allow-listing: `find_multipaths` defaults to
`"no"`, a catch-all **device** blacklist rejects unknown disks, and device
exceptions admit only the selected vendor/product matches. Local root, LVM,
Ceph OSD and Nova disks do not match these profiles. List all arrays needed by
CSI and Cinder on the host; an omitted array is blocked.

The built-in profiles are `netapp_ontap` (SCSI and NVMe), `pure_flasharray`,
`pure_flasharray_nvme`, `nimble`, and `powerstore` (SCSI and NVMe). Existing
Pure and Nimble device settings are retained. Other profiles use the device
settings built into the installed multipath-tools hardware table. Override
`multipathd_array_profiles` to supply additional profiles; each profile has a
`devices` list whose entries contain `vendor`, `product`, and an optional
`settings` mapping. Matches are POSIX extended regular expressions.

With `multipathd_arrays: []`, the legacy policy remains: `find_multipaths yes`,
the existing Pure and Nimble device settings, and the existing Portworx and
VMware exclusions. `multipathd_find_multipaths` can be overridden explicitly;
quote values such as `"yes"` and `"no"`.

`multipathd_blacklist_wwids` remains available for explicitly excluded LUNs.
WWID exclusions still win over device exceptions, so do not put an allowed
array's required LUNs in this list. Do not use a catch-all WWID blacklist:
exceptions only cancel blacklist rules of the same category.

Before enabling array allow-listing on existing hosts, verify the selected
profiles against `multipath -ll` and `multipath -v3 -d`, including local disks.
Validate volume attachment with every array used on a compute host.

When `multipathd_arrays` is set, the role reads `multipath -ll` before writing
the configuration and fails if an active map matches none of the selected
profiles, so attached volumes from an omitted array are not cut off. Maps whose
WWID is in `multipathd_blacklist_wwids` are ignored. Set
`multipathd_check_active_maps: false` only after detaching those volumes.

To add a profile while keeping the built-in ones, combine them:

```yaml
multipathd_array_profiles: >-
  {{ _multipathd_array_profiles | combine({'example': {'devices': [{'vendor': 'EXAMPLE', 'product': 'LUN'}]}}) }}
```
