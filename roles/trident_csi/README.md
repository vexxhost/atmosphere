# `trident_csi`

Installs NetApp Trident as the Kubernetes CSI driver and configures a Trident
backend plus the `general` StorageClass used by Atmosphere services. The role
defaults to `ontap-san` over iSCSI and also supports Fibre Channel with
`trident_csi_access_protocol: fc`, NVMe/TCP with
`trident_csi_access_protocol: nvme`, and ONTAP NAS backends with
`trident_csi_access_protocol: nfs` or `smb`.

The vendored Trident 26.10.0 Helm chart deploys the operator. All required
images, including CSI sidecars and Helm hooks, use the release manifest and
registry mirror settings. `trident_csi_namespace` controls the namespace.
Periodic autosupport reporting is silenced by default.

ONTAP API selection is automatic unless `trident_csi_use_rest` is set; NVMe
requires REST. The default name template includes the storage prefix.

SAN preparation uses the shared `multipathd` role. Configure host-specific
`multipathd_blacklist_wwids` for local root, LVM, and Ceph OSD disks before
enabling SAN multipathing. See the CSI deployment guide for examples.

The CI Kind smoke test in `molecule/csi/trident-smoke.yml` exercises the role
with a dummy backend and `trident_csi_wait_for_backend: false`. It validates
installation and StorageClass creation; real volume I/O needs ONTAP hardware.
