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

// NOTE(mnaser): This is the default mapping for severities, the summary is:
//               - SEV-1: Highest level of severity, indicating an outage
//                        affecting all users. Requires immediate and constant
//                        attention until resolved.
//               - SEV-2: Represents a major functionality broken but not causing
//                        a full outage. Requires prompt attention.
//               - SEV-3: Lowest severity level, indicating minor issues or
//                        functionality impairments that affect some users but
//                        the system is still largely operational.
local defaultSeverityMapping = {
  info: 'SEV-3',
  warning: 'SEV-2',
  critical: 'SEV-1',
};

// NOTE(mnaser): The mapping here follows the format 'AlertName:Severity'. The
//               'Severity' corresponds to the severity level of the alert, and
//               it maps to one of the severity levels defined in
//               defaultSeverityMapping.
local customSeverityMapping = {
  'KubeJobFailed:warning': 'SEV-3',
};

local getSeverity(rule) =
  // Return immediately if the string starts with "SEV-"
  if std.startsWith(rule.labels.severity, 'SEV-') then rule.labels.severity
  else
    local key = rule.alert + ':' + rule.labels.severity;
    if key in customSeverityMapping then customSeverityMapping[key]
    else defaultSeverityMapping[rule.labels.severity];

local mixins = {
  ceph: (import 'vendor/github.com/ceph/ceph/monitoring/ceph-mixin/mixin.libsonnet'),
  coredns: (import 'vendor/github.com/povilasv/coredns-mixin/mixin.libsonnet') + {
    _config+:: {
      corednsSelector: 'job="coredns"',
    },
  },
  kube: (import 'vendor/github.com/kubernetes-monitoring/kubernetes-mixin/mixin.libsonnet') + {
    _config+:: {
      kubeApiserverSelector: 'job="apiserver"',
    },
  },
  memcached: (import 'vendor/github.com/grafana/jsonnet-libs/memcached-mixin/mixin.libsonnet'),
  mysqld: (import 'vendor/github.com/prometheus/mysqld_exporter/mysqld-mixin/mixin.libsonnet') + {
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
  node: (import 'vendor/github.com/prometheus/node_exporter/docs/node-mixin/mixin.libsonnet'),
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
