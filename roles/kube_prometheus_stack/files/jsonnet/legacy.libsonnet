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
        {
          name: 'sel-events-critical',
          rules: [
            // Memory errors - Critical
            {
              alert: 'IpmiSelMemoryUncorrectableError',
              expr: 'increase(ipmi_sel_events_count{name="memory_ecc_uncorrectable"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Uncorrectable memory error detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged uncorrectable memory errors which may indicate imminent memory failure.',
              },
            },
            {
              alert: 'IpmiSelMemoryFailure',
              expr: 'increase(ipmi_sel_events_count{name="memory_dimm_failure"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Memory DIMM failure detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a memory DIMM failure event.',
              },
            },
            // CPU/Processor events - Critical
            {
              alert: 'IpmiSelProcessorThermalTrip',
              expr: 'increase(ipmi_sel_events_count{name="processor_thermal_trip"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Processor thermal trip detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a processor thermal trip event indicating CPU overheating.',
              },
            },
            {
              alert: 'IpmiSelProcessorIerr',
              expr: 'increase(ipmi_sel_events_count{name="processor_ierr"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Processor IERR detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a processor internal error (IERR).',
              },
            },
            {
              alert: 'IpmiSelProcessorFailure',
              expr: 'increase(ipmi_sel_events_count{name="processor_failure"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Processor failure detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a processor failure event.',
              },
            },
            {
              alert: 'IpmiSelMachineCheckException',
              expr: 'increase(ipmi_sel_events_count{name="machine_check_exception"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Machine check exception detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a machine check exception (MCE) indicating a hardware error.',
              },
            },
            // Temperature events - Critical
            {
              alert: 'IpmiSelTemperatureCritical',
              expr: 'increase(ipmi_sel_events_count{name="temperature_critical"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Critical temperature event on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a critical temperature threshold event.',
              },
            },
            {
              alert: 'IpmiSelTemperatureNonRecoverable',
              expr: 'increase(ipmi_sel_events_count{name="temperature_non_recoverable"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Non-recoverable temperature event on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a non-recoverable temperature event.',
              },
            },
            // Power supply events - Critical
            {
              alert: 'IpmiSelPsuFailure',
              expr: 'increase(ipmi_sel_events_count{name="psu_failure"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Power supply failure detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a power supply failure event.',
              },
            },
            {
              alert: 'IpmiSelPsuRedundancyLost',
              expr: 'increase(ipmi_sel_events_count{name="psu_redundancy_lost"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Power supply redundancy lost on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a power supply redundancy lost event.',
              },
            },
            {
              alert: 'IpmiSelPowerUnitFailure',
              expr: 'increase(ipmi_sel_events_count{name="power_unit_failure"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Power unit failure detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a power unit failure event.',
              },
            },
            // Voltage events - Critical
            {
              alert: 'IpmiSelVoltageCritical',
              expr: 'increase(ipmi_sel_events_count{name="voltage_critical"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'Critical voltage event on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a critical voltage threshold event.',
              },
            },
            // System events - Critical
            {
              alert: 'IpmiSelOsCriticalStop',
              expr: 'increase(ipmi_sel_events_count{name="os_critical_stop"}[1h]) > 0',
              labels: {
                severity: 'critical',
              },
              annotations: {
                summary: 'OS critical stop detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged an operating system critical stop event.',
              },
            },
          ],
        },
        {
          name: 'sel-events-warning',
          rules: [
            // Memory errors - Warning
            {
              alert: 'IpmiSelMemoryCorrectableError',
              expr: 'increase(ipmi_sel_events_count{name="memory_ecc_correctable"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Correctable memory error detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged correctable memory errors. Monitor for increasing frequency.',
              },
            },
            {
              alert: 'IpmiSelMemoryConfigurationError',
              expr: 'increase(ipmi_sel_events_count{name="memory_configuration_error"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Memory configuration error on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a memory configuration error event.',
              },
            },
            // Temperature events - Warning
            {
              alert: 'IpmiSelTemperatureWarning',
              expr: 'increase(ipmi_sel_events_count{name="temperature_warning"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Temperature warning event on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a temperature warning threshold event.',
              },
            },
            // Fan events - Warning
            {
              alert: 'IpmiSelFanFailure',
              expr: 'increase(ipmi_sel_events_count{name="fan_failure"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Fan failure detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a fan failure event.',
              },
            },
            {
              alert: 'IpmiSelFanWarning',
              expr: 'increase(ipmi_sel_events_count{name="fan_warning"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Fan warning event on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a fan speed warning event.',
              },
            },
            {
              alert: 'IpmiSelFanRedundancyLost',
              expr: 'increase(ipmi_sel_events_count{name="fan_redundancy_lost"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Fan redundancy lost on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a fan redundancy lost event.',
              },
            },
            // Power supply events - Warning
            {
              alert: 'IpmiSelPsuAcLost',
              expr: 'increase(ipmi_sel_events_count{name="psu_ac_lost"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Power supply AC lost on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a power supply AC lost event.',
              },
            },
            // Disk/Storage events - Warning
            {
              alert: 'IpmiSelDriveFailure',
              expr: 'increase(ipmi_sel_events_count{name="drive_failure"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Drive failure detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a drive failure event.',
              },
            },
            {
              alert: 'IpmiSelDrivePredictiveFailure',
              expr: 'increase(ipmi_sel_events_count{name="drive_predictive_failure"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Drive predictive failure on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a drive predictive failure event. Replace drive soon.',
              },
            },
            {
              alert: 'IpmiSelNvmeTemperatureCritical',
              expr: 'increase(ipmi_sel_events_count{name="nvme_temperature_critical"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'NVMe critical temperature on {{ $labels.instance }}',
                description: 'IPMI SEL has logged an NVMe critical temperature event.',
              },
            },
            // Voltage events - Warning
            {
              alert: 'IpmiSelVoltageWarning',
              expr: 'increase(ipmi_sel_events_count{name="voltage_warning"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Voltage warning event on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a voltage warning threshold event.',
              },
            },
            // Chassis events - Warning
            {
              alert: 'IpmiSelChassisIntrusion',
              expr: 'increase(ipmi_sel_events_count{name="chassis_intrusion"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Chassis intrusion detected on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a chassis intrusion event.',
              },
            },
            // System events - Warning
            {
              alert: 'IpmiSelSystemBootFailure',
              expr: 'increase(ipmi_sel_events_count{name="system_boot_failure"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'System boot failure on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a system boot failure or POST error event.',
              },
            },
            {
              alert: 'IpmiSelWatchdogReset',
              expr: 'increase(ipmi_sel_events_count{name="watchdog_reset"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'Watchdog reset on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a watchdog timer reset event.',
              },
            },
            {
              alert: 'IpmiSelFirmwareError',
              expr: 'increase(ipmi_sel_events_count{name="system_firmware_error"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'System firmware error on {{ $labels.instance }}',
                description: 'IPMI SEL has logged a firmware or BIOS error event.',
              },
            },
            // SEL management - Warning
            {
              alert: 'IpmiSelFull',
              expr: 'increase(ipmi_sel_events_count{name="sel_full"}[1h]) > 0',
              labels: {
                severity: 'warning',
              },
              annotations: {
                summary: 'SEL is full on {{ $labels.instance }}',
                description: 'IPMI SEL is full and needs to be cleared to capture new events.',
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
