local ceph = import 'vendor/ceph-mixin/mixin.libsonnet';

local DISABLED_NODE_ALERTS = [
  // * Dropped `CephNodeDiskspaceWarning` because we already have a
  //   few alerts like `NodeFilesystemSpaceFillingUp`, etc.
  'CephNodeDiskspaceWarning',

  // * Dropped `CephNodeNetworkPacketDrops` due to noisy alerts with
  //   no actionable items to fix it.
  'CephNodeNetworkPacketDrops',
];

local disableAlerts = {
  prometheusAlerts+:: {
    groups: std.map(
      function(group)
        if group.name == 'nodes' then
          group {
            rules: std.filter(
              function(rule)
                std.setMember(rule.alert, DISABLED_NODE_ALERTS) == false,
              group.rules
            ),
          }
        else
          group,
      super.groups
    ),
  },
};

(ceph + disableAlerts)
