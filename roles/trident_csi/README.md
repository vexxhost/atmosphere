# `trident_csi`

Installs NetApp Trident as the Kubernetes CSI driver and configures a Trident
backend plus the `general` StorageClass used by Atmosphere services. The role
defaults to `ontap-san` over iSCSI and also supports Fibre Channel with
`trident_csi_access_protocol: fc`, NVMe/TCP with
`trident_csi_access_protocol: nvme`, and ONTAP NAS backends with
`trident_csi_access_protocol: nfs`.

The vendored Trident 26.10.0 Helm chart deploys the operator. All required
images, including CSI sidecars and Helm hooks, use the release manifest and
registry mirror settings. `trident_csi_namespace` controls the namespace.
Periodic autosupport reporting is silenced by default.

ONTAP API selection is automatic unless `trident_csi_use_rest` is set; NVMe
requires REST. The default name template includes the storage prefix.

The CSI playbook prepares controllers before installing the operator. The
operator, controller plugin and node plugin are scheduled with
`trident_csi_node_selector`, which defaults to `openstack-control-plane:
enabled`, the label carried by controllers. Compute nodes are left to the
`multipathd` and `iscsi` roles for Cinder. Host preparation installs NFS
clients, sets iSCSI session scanning to manual, and configures NVMe/TCP modules
and persistent host NQNs as appropriate. Existing initiator names are
preserved; duplicate iSCSI IQNs or NVMe NQNs among controllers fail validation.

For SAN backends, put `netapp_ontap` in each controller's `multipathd_arrays`
inventory variable, alongside every other array the node uses. The shared `multipathd`
role allows only those array devices, protecting local disks without a
per-host WWID inventory. The same inventory applies to CSI and standalone
OpenStack runs. See `roles/multipathd/README.md` and the CSI deployment guide.

When invoking this role directly, it prepares the hosts in the current play by
default. To prepare a separate node play, use `tasks_from: prepare`; it performs
no chart upload or Kubernetes API calls. Set `trident_csi_prepare_hosts: false`
for the subsequent controller deployment. Keep the default linear strategy so
all node identifiers are collected before the uniqueness check. If multipath
is managed externally, `trident_csi_configure_multipath: false` skips writing
its configuration; the SAN inventory assertions still apply.

The `trident / smoke` workflow job installs the role into a disposable Kind
cluster using a custom namespace, a dummy backend, and
`trident_csi_wait_for_backend: false`. It runs only when Trident-related files
change. It checks installation readiness, the
StorageClass, and the pinned images in controller pods and the Linux node
DaemonSet. Host preparation is skipped because the runner is not a cluster
node. Run it with
`ansible-playbook -i localhost, molecule/csi/trident-smoke.yml`.

Volume creation, attachment and I/O require real ONTAP hardware. Before merging,
validate an ONTAP LUN alongside a local disk using `multipath -ll` and
`multipath -v3 -d`, and test Cinder attachment on a compute with a second array.
