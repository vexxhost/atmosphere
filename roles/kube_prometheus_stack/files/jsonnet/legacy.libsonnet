{
  'ethtool-exporter': {
    groups: [
      {
        name: 'rules',
        rules: [
          {
            alert: 'EthernetReceiveDiscards',
            expr: 'rate(node_net_ethtool{type="rx_discards"}[1m]) > 0',
            labels: {
              severity: 'warning',
            },
          },
        ],
      },
    ],
  },
  'ipmi-exporter': {
    groups: [
      {
        name: 'rules',
        rules: [
          {
            alert: 'IpmiCollectorDown',
            expr: 'ipmi_up == 0',
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
  'node-exporter-local': {
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
            alert: 'NodeHighMemoryUsage',
            expr: '(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 < 2.5',
            'for': '2m',
            labels: {
              severity: 'critical',
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
              severity: 'SEV-3',
            },
          },
          {
            alert: 'NodeNonLTSKernel',
            expr: 'node_uname_info{release!~"^5.(4|15).*"}',
            labels: {
              severity: 'SEV-3',
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
          local recordingRule(metric, expr) = {
            record: 'node:softnet:' + metric + ':1m',
            expr: expr,
          };
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
                '0': 'SEV-3',
                '0.5': 'SEV-2',
                '0.75': 'SEV-1',
              }[nodesAffected],
            },
          };
          [
            recordingRule('backlog', 'sum(node_softnet_backlog_len) by (instance)'),
            alertRule('backlog', '5000', '0'),
            alertRule('backlog', '5000', '0.5'),
            alertRule('backlog', '5000', '0.75'),

            recordingRule('squeezed', 'sum(rate(node_softnet_times_squeezed_total[1m])) by (instance)'),
            alertRule('squeezed', '0', '0'),

            recordingRule('dropped', 'sum(rate(node_softnet_dropped_total[1m])) by (instance)'),
            alertRule('dropped', '0', '0'),
            alertRule('dropped', '0', '0.5'),
            alertRule('dropped', '0', '0.75'),
          ],
      },
    ],
  },
  'openstack-exporter': {
    groups: [
      {
        name: 'cinder',
        rules: [
          {
            alert: 'CinderAgentDown',
            annotations: {
              description: 'The service {{ $labels.exported_service }} running on {{ $labels.hostname }} is being reported as down.',
              summary: '[{{ $labels.hostname }}] {{ $labels.exported_service }} down',
            },
            expr: 'openstack_cinder_agent_state != 1',
            labels: {
              severity: 'warning',
            },
          },
          {
            alert: 'CinderAgentDown',
            annotations: {
              description: 'The service {{ $labels.exported_service }} running on {{ $labels.hostname }} is being reported as down for 5 minutes. This can affect volume operations so it must be resolved as quickly as possible.',
              summary: '[{{ $labels.hostname }}] {{ $labels.exported_service }} down',
            },
            expr: 'openstack_cinder_agent_state != 1',
            'for': '5m',
            labels: {
              severity: 'critical',
            },
          },
          {
            alert: 'CinderAgentDisabled',
            annotations: {
              description: 'The service {{ $labels.exported_service }} running on {{ $labels.hostname }} has been disabled for 60 minutes.  This can affect volume operations so it must be resolved as quickly as possible.',
              summary: '[{{ $labels.hostname }}] {{ $labels.exported_service }} disabled',
            },
            expr: 'openstack_cinder_agent_state{adminState!="enabled"}',
            'for': '1h',
            labels: {
              severity: 'warning',
            },
          },
          {
            alert: 'CinderVolumeInError',
            annotations: {
              description: 'The volume {{ $labels.id }} has been in ERROR state for over 24 hours. It must be cleaned up or removed in order to provide a consistent customer experience.',
              summary: '[{{ $labels.id }}] Volume in ERROR statef endraw %}',
            },
            expr: 'openstack_cinder_volume_status{status=~"error.*"}',
            'for': '24h',
            labels: {
              severity: 'warning',
            },
          },
        ],
      },
      {
        name: 'neutron',
        rules: [
          {
            alert: 'NeutronAgentDown',
            annotations: {
              description: 'The service {{ $labels.exported_service }} running on {{ $labels.hostname }} is being reported as down.',
              summary: '[{{ $labels.hostname }}] {{ $labels.exported_service }} down',
            },
            expr: 'openstack_neutron_agent_state != 1',
            labels: {
              severity: 'warning',
            },
          },
          {
            alert: 'NeutronAgentDown',
            annotations: {
              description: 'The service {{ $labels.exported_service }} running on {{ $labels.hostname }} is being reported as down for 5 minutes. This can affect network operations so it must be resolved as quickly as possible.',
              summary: '[{{ $labels.hostname }}] {{ $labels.exported_service }} down',
            },
            expr: 'openstack_neutron_agent_state != 1',
            'for': '5m',
            labels: {
              severity: 'critical',
            },
          },
          {
            alert: 'NeutronAgentDisabled',
            annotations: {
              description: 'The service {{ $labels.exported_service }} running on {{ $labels.hostname }} has been disabled for 60 minutes.  This can affect network operations so it must be resolved as quickly as possible.',
              summary: '[{{ $labels.hostname }}] {{ $labels.exported_service }} disabled',
            },
            expr: 'openstack_neutron_agent_state{adminState!="up"}',
            'for': '1h',
            labels: {
              severity: 'warning',
            },
          },
          {
            alert: 'NeutronBindingFailedPorts',
            annotations: {
              description: 'The NIC {{ $labels.mac_address }} of {{ $labels.device_owner }} has binding failed port now.',
              summary: '[{{ $labels.device_owner }}] {{ $labels.mac_address }} binding failed',
            },
            expr: 'openstack_neutron_port{binding_vif_type="binding_failed"} != 0',
            labels: {
              severity: 'warning',
            },
          },
          {
            alert: 'NeutronNetworkOutOfIPs',
            annotations: {
              description: 'The subnet {{ $labels.subnet_name }} within {{ $labels.network_name }} is currently at {{ $value }}% utilization.  If the IP addresses run out, it will impact the provisioning of new ports.',
              summary: '[{{ $labels.network_name }}] {{ $labels.subnet_name }} running out of IPs',
            },
            expr: 'sum by (network_id) (openstack_neutron_network_ip_availabilities_used{project_id!=""}) / sum by (network_id) (openstack_neutron_network_ip_availabilities_total{project_id!=""}) * 100 > 80',
            labels: {
              severity: 'warning',
            },
          },
        ],
      },
      {
        name: 'nova',
        rules: [
          {
            alert: 'NovaAgentDown',
            annotations: {
              description: 'The service {{ $labels.exported_service }} running on {{ $labels.hostname }} is being reported as down.',
              summary: '[{{ $labels.hostname }}] {{ $labels.exported_service }} down',
            },
            expr: 'openstack_nova_agent_state != 1',
            labels: {
              severity: 'warning',
            },
          },
          {
            alert: 'NovaAgentDown',
            annotations: {
              description: 'The service {{ $labels.exported_service }} running on {{ $labels.hostname }} is being reported as down.  This can affect compute operations so it must be resolved as quickly as possible.',
              summary: '[{{ $labels.hostname }}] {{ $labels.exported_service }} down',
            },
            expr: 'openstack_nova_agent_state != 1',
            'for': '5m',
            labels: {
              severity: 'critical',
            },
          },
          {
            alert: 'NovaAgentDisabled',
            annotations: {
              description: 'The service {{ $labels.exported_service }} running on {{ $labels.hostname }} has been disabled for 60 minutes.  This can affect compute operations so it must be resolved as quickly as possible.',
              summary: '[{{ $labels.hostname }}] {{ $labels.exported_service }} disabled',
            },
            expr: 'openstack_nova_agent_state{adminState!="enabled"}',
            'for': '1h',
            labels: {
              severity: 'warning',
            },
          },
          {
            alert: 'NovaInstanceInError',
            annotations: {
              description: 'The instance {{ $labels.id }} has been in ERROR state for over 24 hours. It must be cleaned up or removed in order to provide a consistent customer experience.',
              summary: '[{{ $labels.id }}] Instance in ERROR state',
            },
            expr: 'openstack_nova_server_status{status="ERROR"}',
            'for': '24h',
            labels: {
              severity: 'warning',
            },
          },
          {
            alert: 'NovaFailureRisk',
            annotations: {
              description: 'The cloud capacity will be at {{ $value }} in the event of the failure of a single hypervisor which puts the cloud at risk of not being able to recover should any hypervisor failures occur.  Please ensure that adequate amount of infrastructure is assigned to this deployment to prevent this.',
              summary: '[nova] Failure risk',
            },
            expr: '(sum(openstack_nova_memory_available_bytes-openstack_nova_memory_used_bytes) - max(openstack_nova_memory_used_bytes)) / sum(openstack_nova_memory_available_bytes-openstack_nova_memory_used_bytes) * 100 < 0.25',
            'for': '6h',
            labels: {
              severity: 'warning',
            },
          },
          {
            alert: 'NovaCapacity',
            annotations: {
              description: 'The cloud capacity is currently at `{{ $value }}` which means there is a risk of running out of capacity due to the timeline required to add new nodes. Please ensure that adequate amount of infrastructure is assigned to this deployment to prevent this.',
              summary: '[nova] Capacity risk',
            },
            expr: 'sum (     openstack_nova_memory_used_bytes   + on(hostname) group_left(adminState)     (0 * openstack_nova_agent_state{exported_service="nova-compute",adminState="enabled"}) ) / sum (     openstack_nova_memory_available_bytes   + on(hostname) group_left(adminState)     (0 * openstack_nova_agent_state{exported_service="nova-compute",adminState="enabled"}) ) * 100 > 75',
            'for': '6h',
            labels: {
              severity: 'warning',
            },
          },
        ],
      },
    ],
  },
  rabbitmq: {
    groups: [
      {
        name: 'recording',
        rules: [
          {
            record: 'rabbitmq:usage:memory',
            labels: {
              job: 'rabbitmq',
            },
            expr: 'sum without (job) (   rabbitmq_process_resident_memory_bytes ) / sum without (   container,   pod,   job,   namespace,   node,   resource,   uid,   unit ) (   label_replace(     cluster:namespace:pod_memory:active:kube_pod_container_resource_limits,     "instance",     "$1",     "pod",     "(.*)"   ) )',
          },
        ],
      },
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
}
