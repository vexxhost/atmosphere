// NOTE(mnaser): The following are a list of disabled alerts known to be noisy
//               or not useful.
local disabledAlerts = [
  // * Dropped `CephNodeDiskspaceWarning` because we already have a
  //   few alerts like `NodeFilesystemSpaceFillingUp`, etc.
  'CephNodeDiskspaceWarning',

  // * Dropped `CephNodeNetworkPacketDrops` due to noisy alerts with
  //   no actionable items to fix it.
  'CephNodeNetworkPacketDrops',
];

// NOTE(mnaser): This is the default mapping for severities:
//               - P1: Full service disruption or significant loss of
//                     functionality. Requires immediate action.
//               - P2: Major functionality broken, affecting large group of
//                     users or critical components. Prompt attention needed.
//               - P3: Issues affecting smaller group of users or a single
//                     system. Attention required during business hours.
//               - P4: Minor issues with limited impact. Attention and potential
//                     action needed during standard business hours.
//               - P5: Normal activities or minor issues. Typically no immediate
//                     attention or action required.
local defaultSeverityMapping = {
  critical: 'P1',
  warning: 'P3',
  info: 'P5',
};

// NOTE(mnaser): The mapping here follows the format 'AlertName:Severity'. The
//               'Severity' corresponds to the severity level of the alert, and
//               it maps to one of the severity levels defined in
//               defaultSeverityMapping.
local customSeverityMapping = {
  'CephMgrPrometheusModuleInactive:critical': 'P4',
  'CephMonDown:warning': 'P4',
  'CephMonDownQuorumAtRisk:critical': 'P3',
  'CephOSDTimeoutsClusterNetwork:warning': 'P4',
  'CephOSDTimeoutsPublicNetwork:warning': 'P4',
  'KubeJobFailed:warning': 'P4',
};

local getSeverity(rule) =
  // Return immediately if the string starts with "P"
  if std.startsWith(rule.labels.severity, 'P') then rule.labels.severity
  else
    local key = rule.alert + ':' + rule.labels.severity;
    if key in customSeverityMapping then customSeverityMapping[key]
    else defaultSeverityMapping[rule.labels.severity];

local mixins = {
  alertmanager: (import 'alertmanager-mixin/mixin.libsonnet') + {
    _config+:: {
      alertmanagerSelector: 'job="kube-prometheus-stack-alertmanager"',
    },
  },
  ceph: (import 'ceph-mixin/mixin.libsonnet'),
  coredns: (import 'coredns-mixin/mixin.libsonnet') + {
    _config+:: {
      corednsSelector: 'job="coredns"',
    },
  },
  kube: (import 'kubernetes-mixin/mixin.libsonnet') + {
    _config+:: {
      kubeApiserverSelector: 'job="apiserver"',
    },
  },
  memcached: (import 'memcached-mixin/mixin.libsonnet'),
  mysqld: (import 'mysqld-mixin/mixin.libsonnet') + {
    prometheusAlerts+:: {
      groups+: [
        {
          name: 'mysqld-extras',
          rules: [
            {
              alert: 'MysqlTooManyConnections',
              'for': '1m',
              expr: |||
                max_over_time(mysql_global_status_threads_connected[1m]) / mysql_global_variables_max_connections * 100 > 80
              |||,
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'MysqlHighThreadsRunning',
              'for': '1m',
              expr: |||
                max_over_time(mysql_global_status_threads_running[1m]) / mysql_global_variables_max_connections * 100 > 60
              |||,
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'MysqlSlowQueries',
              'for': '2m',
              expr: |||
                increase(mysql_global_status_slow_queries[1m]) > 0
              |||,
              labels: {
                severity: 'warning',
              },
            },
          ],
        },
      ],
    },
  },
  node: (import 'node-mixin/mixin.libsonnet'),
  openstack: (import 'openstack.libsonnet'),
} + (import 'legacy.libsonnet');

{
  [key]: mixins[key] {
    prometheusAlerts: {
      groups: [
        {
          name: group.name,
          rules: [
            rule {
              labels+: {
                severity: getSeverity(rule),
              },
            }
            for rule in group.rules
            if !std.member(disabledAlerts, rule.alert)
          ],
        }
        for group in mixins[key].prometheusAlerts.groups
      ],
    },
  }
  for key in std.objectFields(mixins)
}
