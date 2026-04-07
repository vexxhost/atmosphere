{
  'ipmi-exporter': {
    prometheusAlerts+:: {
      groups: [
        {
          name: 'rules',
          rules: [
            {
              alert: 'IpmiCollectorDown',
              'for': '15m',
              expr: 'ipmi_up == 0',
              labels: {
                severity: 'warning',
              },
            },
          ],
        },
        {
          name: 'collectors-state-warning',
          rules: [
            {
              alert: 'IpmiCurrent',
              expr: 'ipmi_current_state == 1',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'IpmiFanSpeed',
              expr: 'ipmi_fan_speed_state == 1',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'IpmiPower',
              expr: 'ipmi_power_state == 1',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'IpmiSensor',
              expr: 'ipmi_sensor_state == 1',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'IpmiTemperature',
              expr: 'ipmi_temperature_state == 1',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'IpmiVoltage',
              expr: 'ipmi_voltage_state == 1',
              labels: {
                severity: 'warning',
              },
            },
          ],
        },
        {
          name: 'collectors-state-critical',
          rules: [
            {
              alert: 'IpmiCurrent',
              expr: 'ipmi_current_state == 2',
              labels: {
                severity: 'critical',
              },
            },
            {
              alert: 'IpmiFanSpeed',
              expr: 'ipmi_fan_speed_state == 2',
              labels: {
                severity: 'critical',
              },
            },
            {
              alert: 'IpmiPower',
              expr: 'ipmi_power_state == 2',
              labels: {
                severity: 'critical',
              },
            },
            {
              alert: 'IpmiSensor',
              expr: 'ipmi_sensor_state{name!="TPM Presence"} == 2',
              labels: {
                severity: 'critical',
              },
            },
            {
              alert: 'IpmiTemperature',
              expr: 'ipmi_temperature_state == 2',
              labels: {
                severity: 'critical',
              },
            },
            {
              alert: 'IpmiVoltage',
              expr: 'ipmi_voltage_state == 2',
              labels: {
                severity: 'critical',
              },
            },
          ],
        },
      ],
    },
  },
  'node-exporter-local': {
    prometheusRules+:: {
      groups: [
        {
          name: 'softnet.rules',
          rules:
            local recordingRule(metric, expr) = {
              record: 'node:softnet:' + metric + ':1m',
              expr: expr,
            };
            [
              recordingRule('backlog', 'sum(node_softnet_backlog_len) by (instance)'),
              recordingRule('dropped', 'sum(rate(node_softnet_dropped_total[1m])) by (instance)'),
            ],
        },
      ],
    },
    prometheusAlerts+:: {
      groups: [
        {
          name: 'node',
          rules: [
            {
              alert: 'NodeHighLoadAverage',
              expr: 'node_load5 / count(node_cpu_seconds_total{mode="system"}) without (cpu, mode) > 1.5',
              'for': '30m',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'NodeHighCpuUsage',
              expr: "sum by(instance)(irate(node_cpu_seconds_total{mode='idle'}[5m])) < 1",
              'for': '2m',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'NodeLowEntropy',
              expr: 'node_entropy_available_bits / node_entropy_pool_size_bits < 0.20',
              'for': '5m',
              labels: {
                severity: 'P5',
              },
            },
          ],
        },
        {
          name: 'network',
          rules: [
            {
              alert: 'NodeNetworkMulticast',
              expr: 'rate(node_network_receive_multicast_total[1m]) > 1000',
              'for': '5m',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'High multicast traffic on node {{ $labels.instance }}: {{ $value }} packets/sec',
                description: 'This can result in high software interrupt load on the node which can bring network performance down.',
                runbook_url: 'https://github.com/vexxhost/atmosphere/tree/main/roles/kube_prometheus_stack#NodeNetworkMulticast',
              },
            },
          ],
        },
        {
          name: 'softnet',
          rules:
            local capitalize(s) = std.asciiUpper(std.substr(s, 0, 1)) + std.substr(s, 1, std.length(s) - 1);
            local alertRule(metric, threshold, nodesAffected) = {
              alert: {
                '0': 'SingleNodeSoftNet' + capitalize(metric),
                '0.5': 'MultipleNodesSoftNet' + capitalize(metric),
                '0.75': 'MajorityNodesSoftNet' + capitalize(metric),
              }[nodesAffected],
              expr: 'count(node:softnet:%s:1m > %s) > (count(node:softnet:%s:1m) * %s)' % [metric, threshold, metric, nodesAffected],
              'for': '1m',
              labels: {
                severity: {
                  '0': 'P3',
                  '0.5': 'P2',
                  '0.75': 'P1',
                }[nodesAffected],
              },
            };
            [
              alertRule('backlog', '5000', '0'),
              alertRule('backlog', '5000', '0.5'),
              alertRule('backlog', '5000', '0.75'),
              alertRule('dropped', '0', '0'),
              alertRule('dropped', '0', '0.5'),
              alertRule('dropped', '0', '0.75'),
            ],
        },
      ],
    },
  },
  rabbitmq: {
    prometheusRules+:: {
      groups: [
        {
          name: 'recording',
          rules:
            [
              {
                record: 'rabbitmq:usage:memory',
                labels: {
                  job: 'rabbitmq',
                },
                expr: 'sum without (job) (   rabbitmq_process_resident_memory_bytes ) / sum without (   container,   pod,   job,   namespace,   node,   resource,   uid,   unit ) (   label_replace(     cluster:namespace:pod_memory:active:kube_pod_container_resource_limits,     "instance",     "$1",     "pod",     "(.*)"   ) )',
              },
            ],
        },
      ],
    },
    prometheusAlerts+:: {
      groups: [
        {
          name: 'alarms',
          rules: [
            {
              alert: 'RabbitmqAlarmFreeDiskSpace',
              expr: 'rabbitmq_alarms_free_disk_space_watermark == 1',
              labels: {
                severity: 'critical',
              },
            },
            {
              alert: 'RabbitmqAlarmMemoryUsedWatermark',
              expr: 'rabbitmq_alarms_memory_used_watermark == 1',
              labels: {
                severity: 'critical',
              },
            },
            {
              alert: 'RabbitmqAlarmFileDescriptorLimit',
              expr: 'rabbitmq_alarms_file_descriptor_limit == 1',
              labels: {
                severity: 'critical',
              },
            },
          ],
        },
        {
          name: 'limits',
          rules: [
            {
              alert: 'RabbitmqMemoryHigh',
              expr: 'rabbitmq:usage:memory > 0.80',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'RabbitmqMemoryHigh',
              expr: 'rabbitmq:usage:memory > 0.95',
              labels: {
                severity: 'critical',
              },
            },
            {
              alert: 'RabbitmqFileDescriptorsUsage',
              expr: 'rabbitmq_process_open_fds / rabbitmq_process_max_fds > 0.80',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'RabbitmqFileDescriptorsUsage',
              expr: 'rabbitmq_process_open_fds / rabbitmq_process_max_fds > 0.95',
              labels: {
                severity: 'critical',
              },
            },
            {
              alert: 'RabbitmqTcpSocketsUsage',
              expr: 'rabbitmq_process_open_tcp_sockets / rabbitmq_process_max_tcp_sockets > 0.80',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'RabbitmqTcpSocketsUsage',
              expr: 'rabbitmq_process_open_tcp_sockets / rabbitmq_process_max_tcp_sockets > 0.95',
              labels: {
                severity: 'critical',
              },
            },
          ],
        },
        {
          name: 'msgs',
          rules: [
            {
              alert: 'RabbitmqUnackedMessages',
              expr: 'sum(rabbitmq_queue_messages_unacked) BY (queue) > 1000',
              'for': '5m',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'RabbitmqUnackedMessages',
              expr: 'sum(rabbitmq_queue_messages_unacked) BY (queue) > 1000',
              'for': '1h',
              labels: {
                severity: 'critical',
              },
            },
          ],
        },
      ],
    },
  },
}
