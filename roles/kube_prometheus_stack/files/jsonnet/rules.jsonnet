local legacy = import 'legacy.libsonnet';

local ceph = import 'ceph.libsonnet';
local mysqld = import 'mysqld.libsonnet';
local memcached = import 'vendor/github.com/grafana/jsonnet-libs/memcached-mixin/mixin.libsonnet';

local coredns = (import 'vendor/github.com/povilasv/coredns-mixin/mixin.libsonnet') + {
  _config+:: {
    corednsSelector: 'job="coredns"',
  },
};

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

local node = import 'vendor/github.com/prometheus/node_exporter/docs/node-mixin/mixin.libsonnet';

local alerts = {
  ceph: ceph.prometheusAlerts,
  coredns: coredns.prometheusAlerts,
  memcached: memcached.prometheusAlerts,
  'percona-xtradb-pxc': mysqld.prometheusAlerts,
  node: node.prometheusAlerts,
} + legacy;

{
  [key]: {
    groups: [
      {
        name: group.name,
        rules: [
          if 'alert' in rule then
            rule {
              labels+: {
                severity: getSeverity(rule),
              },
            }
          else
            rule
          for rule in group.rules
        ],
      }
      for group in alerts[key].groups
    ],
  }
  for key in std.objectFields(alerts)
  if std.objectHas(alerts, key)
}
