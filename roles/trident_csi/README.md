# `trident_csi`

Installs NetApp Trident as the Kubernetes CSI driver and configures a Trident
backend plus the `general` StorageClass used by Atmosphere services. The role
defaults to `ontap-san` over iSCSI and also supports Fibre Channel with
`trident_csi_access_protocol: fc`.
