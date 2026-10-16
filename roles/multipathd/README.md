# `multipath-tools` for Linux

This role manage `multipath-tools` package and its configuration.

`multipathd_find_multipaths` defaults to `"yes"`. When `csi_driver: trident`
uses SAN host preparation with multipath configuration enabled, it follows
`trident_csi_multipath_find_multipaths` (default: `"no"`) so later OpenStack
configuration preserves Trident's setting. This also applies when running the
OpenStack playbook separately. Set `multipathd_find_multipaths` explicitly to
override the generic role's setting, and quote values such as `"yes"` and `"no"`.
