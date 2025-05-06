// NOTE(mnaser): The following are a list of disabled alerts known to be noisy
//               or not useful.
local disabledAlerts = [
  // * Dropped `CephNodeDiskspaceWarning` because we already have a
  //   few alerts like `NodeFilesystemSpaceFillingUp`, etc.
  'CephNodeDiskspaceWarning',

  // * Dropped `CephNodeNetworkPacketDrops` due to noisy alerts with
  //   no actionable items to fix it.
  'CephNodeNetworkPacketDrops',

  // Superseded by CephHealthDetail* alerts
  'CephHealthWarning',
  'CephHealthError',

  // * Dropped `CephPGImbalance`
  // the balancer module takes care of this
  'CephPGImbalance',

  // * Dropped `MySQLDown` due to noisy alerts even
  //   the replication still more than minimum
  'MySQLDown',
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
  alertmanager: (import 'vendor/github.com/prometheus/alertmanager/doc/alertmanager-mixin/mixin.libsonnet') + {
    _config+:: {
      alertmanagerSelector: 'job="kube-prometheus-stack-alertmanager",namespace="monitoring"',
      alertmanagerClusterLabels: 'namespace,service,cluster',
    },
  },
  ceph: (import 'vendor/github.com/ceph/ceph/monitoring/ceph-mixin/mixin.libsonnet') + {
    prometheusAlerts+:: {
      groups+: [
        {
          name: 'cluster health detail',
          rules: [
            {
              alert: 'CephHealthDetailError',
              'for': '5m',
              expr: 'ceph_health_detail{severity="HEALTH_ERROR"} == 1',
              labels: { severity: 'critical' },
              annotations: {
                summary: 'Ceph is in the ERROR state',
                description: "Health check {{ $labels.name }} has been HEALTH_ERROR for more than 5 minutes. Please check 'ceph health detail' for more information.",
              },
            },
            {
              alert: 'CephHealthDetailWarning',
              'for': '15m',
              expr: 'ceph_health_detail{severity="HEALTH_WARN"} == 1',
              labels: { severity: 'warning' },
              annotations: {
                summary: 'Ceph is in the WARNING state',
                description: "Health check {{ $labels.name }} has been HEALTH_WARN for more than 15 minutes. Please check 'ceph health detail' for more information.",
              },
            },
          ],
        },
        {
          name: 'bluestore-fragmentation-rating',
          rules: [
            {
              alert: 'BluestoreFragmentationRateingConsiderable',
              annotations: {
                description: 'Bluestore fragmentation rating for OSD {{ $labels.osd }} on host {{ $labels.instance }} is currently at {{ $value }}. If it continue to goes higher then 0.9, it will impact other running services.',
                summary: '[{{ $labels.osd }}] reaching a considerable value: {{ $value }}',
              },
              'for': '1m',
              expr: |||
                ceph_osd_fragmentation_rating > 0.7
              |||,
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'BluestoreFragmentationRateingHigh',
              annotations: {
                description: 'Bluestore fragmentation rating for OSD {{ $labels.osd }} on host {{ $labels.instance }} is currently at {{ $value }}. It might impact other running services.',
                summary: '[{{ $labels.osd }}] reaching a high value: {{ $value }}',
              },
              'for': '1m',
              expr: |||
                ceph_osd_fragmentation_rating > 0.9
              |||,
              labels: {
                severity: 'P3',
              },
            }
          ],
        },
      ],
    }
  },
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
            {
              alert: 'MysqlClusterDown',
              'for': '5m',
              expr: 'mysql_up == 0',
              labels: { severity: 'info' },
              annotations: {
                summary: 'Percona XtraDB Cluster replica is down',
                description: "{{ $labels.instance }} replica is down.",
              },
            },
            {
              alert: 'MysqlClusterDown',
              'for': '5m',
              expr: 'round(count(mysql_up==1) / count(mysql_up) * 100) <= 50',
              labels: { severity: 'warning' },
              annotations: {
                summary: 'Percona XtraDB Cluster replicas are down',
                description: "{{ $value }}% of replicas are online.",
              },
            },
            {
              alert: 'MysqlClusterDown',
              'for': '1m',
              expr: 'count(mysql_up==0) == count(mysql_up)',
              labels: { severity: 'critical' },
              annotations: {
                summary: 'Percona XtraDB Cluster is down',
                description: "All replicas are down.",
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
