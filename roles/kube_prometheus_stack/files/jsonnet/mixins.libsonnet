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
      alertmanagerSelector: 'job="kube-prometheus-stack-alertmanager"',
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
      ],
    },
  },
  coredns: (import 'coredns.libsonnet'),
  kube: (import 'vendor/github.com/kubernetes-monitoring/kubernetes-mixin/mixin.libsonnet') + {
    _config+:: {
      kubeApiserverSelector: 'job="apiserver"',
    },
  },
  memcached: (import 'vendor/github.com/grafana/jsonnet-libs/memcached-mixin/mixin.libsonnet'),
  mysqld:
    local base = (import 'vendor/github.com/prometheus/mysqld_exporter/mysqld-mixin/mixin.libsonnet');
    base {
      prometheusAlerts:: {
        groups: [
          if group.name == 'GaleraAlerts' then group {
            rules: [
              if rule.alert == 'MySQLGaleraOutOfSync' then {
                alert: 'MySQLGaleraOutOfSync',
                'for': '15m',
                expr: |||
                  (mysql_global_status_wsrep_local_state != 4 and mysql_global_status_wsrep_local_state != 2 and mysql_global_variables_wsrep_desync == 0)
                |||,
                labels: { severity: 'warning' },
                annotations: {
                  summary: 'Percona XtraDB Cluster: Galera node not in sync with cluster',
                  description: 'The Galera node {{ $labels.instance }} has wsrep_local_state={{ $value }} which is not the expected value of 4 (Synced).  The node is not in Donor state (2) and wsrep_desync is not enabled, indicating an unexpected loss of cluster sync.  Normal behavior is wsrep_local_state=4 for all nodes not actively serving as SST donors.',
                  runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#mysqlgaleraoutofsync',
                },
              } else rule
              for rule in group.rules
            ],
          } else group
          for group in base.prometheusAlerts.groups
        ] + [
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
                description: '{{ $labels.instance }} replica is down.',
              },
            },
            {
              alert: 'MysqlClusterDown',
              'for': '5m',
              expr: 'round(count(mysql_up==1) / count(mysql_up) * 100) <= 50',
              labels: { severity: 'warning' },
              annotations: {
                summary: 'Percona XtraDB Cluster replicas are down',
                description: '{{ $value }}% of replicas are online.',
              },
            },
            {
              alert: 'MysqlClusterDown',
              'for': '1m',
              expr: 'count(mysql_up==0) == count(mysql_up)',
              labels: { severity: 'critical' },
              annotations: {
                summary: 'Percona XtraDB Cluster is down',
                description: 'All replicas are down.',
              },
            },
          ],
        },
      ],
    },
  },
  node:
    (import 'vendor/github.com/prometheus/node_exporter/docs/node-mixin/mixin.libsonnet') {
      _config+:: {
        nodeExporterSelector: 'job="node-exporter"',
      },
      prometheusAlerts+:: {
        groups+: [
          {
            name: 'node-exporter-extras',
            rules: [
              {
                alert: 'NodeTimeSkewDetected',
                expr: |||
                  abs(timestamp(node_time_seconds{%(nodeExporterSelector)s}) - node_time_seconds{%(nodeExporterSelector)s}) > 1
                ||| % mixins.node._config,
                'for': '5m',
                labels: {
                  severity: 'warning',
                },
                annotations: {
                  summary: 'Node {{ $labels.instance }} has a time difference.',
                  description: 'Node {{ $labels.instance }} has a time difference {{ $value }}.',
                },
              },
            ],
          },
        ],
      },
    },
  goldpinger: (import 'goldpinger.libsonnet'),
  nginx: (import 'nginx.libsonnet'),
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
