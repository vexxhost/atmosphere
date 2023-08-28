local node = import 'vendor/github.com/prometheus/node_exporter/docs/node-mixin/mixin.libsonnet';

local alertList = [
  { alert: rule.alert, severity: rule.labels.severity }
  for group in node.prometheusAlerts.groups
  for rule in group.rules
  if 'alert' in rule
];

local defaultSeverityMapping = {
  info: 'SEV-3',
  warning: 'SEV-2',
  critical: 'SEV-1',
};

local customSeverityMapping = {
  // 'NodeFilesystemSpaceFillingUp:warning': 'SEV-3',
};

local getSeverity(rule) =
  local key = rule.alert + ':' + rule.labels.severity;
  if key in customSeverityMapping then customSeverityMapping[key]
  else defaultSeverityMapping[rule.labels.severity];

{
  prometheusAlerts: {
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
      for group in node.prometheusAlerts.groups
    ],
  },
}
