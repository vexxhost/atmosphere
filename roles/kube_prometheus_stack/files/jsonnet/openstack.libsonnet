{
  prometheusRules+:: {
    groups: [
      {
        name: 'neutron',
        rules:
          [
            {
              record: 'neutron:agent:state',
              expr: 'max_over_time(openstack_neutron_agent_state[30m:5m])',
            },
          ],
      },
      {
        name: 'cinder',
        rules:
          [
            {
              record: 'cinder:agent:state',
              expr: 'max_over_time(openstack_cinder_agent_state[30m:5m])',
            },
            {
              record: 'cinder:volume:error',
              expr: 'openstack_cinder_volume_status{status=~"error.*"}',
            },
          ],
      },
      {
        name: 'nova',
        rules:
          [
            {
              record: 'nova:service:state',
              expr: 'max_over_time(openstack_nova_agent_state[30m:5m])',
            },
            {
              record: 'nova:instance:error',
              expr: 'openstack_nova_server_status{status="ERROR"}',
            },
          ],
      },
    ],
  },
  prometheusAlerts+:: {
    groups: [
      {
        name: 'cinder',
        rules: [
          {
            alert: 'CinderAgentDisabled',
            expr: 'cinder:agent:state{adminState!="enabled"} > 0',
            'for': '24h',
            labels: {
              severity: 'SEV-3',
            },
            annotations: {
              summary: 'Cinder agent disabled',
              description: 'A Cinder agent has been administratively disabled for more than 24 hours.',
            },
          },
          {
            alert: 'CinderAgentDown',
            expr: 'cinder:agent:state != 1',
            'for': '15m',
            labels: {
              severity: 'SEV-2',
            },
            annotations: {
              summary: 'Cinder agent down',
              description: 'A Cinder agent has been down for more than 15 minutes.',
            },
          },
          {
            alert: 'CinderAgentGroupDown',
            expr: 'min by (exported_service) (cinder:agent:state) == 0',
            'for': '5m',
            labels: {
              severity: 'SEV-1',
            },
            annotations: {
              summary: 'Cinder agent group down',
              description: 'All instances of a specific Cinder agent have been down for more than 5 minutes.',
            },
          },
          {
            alert: 'CinderVolumeError',
            expr: 'cinder:volume:error > 0',
            'for': '24h',
            labels: {
              severity: 'SEV-3',
            },
            annotations: {
              summary: 'Cinder volume error',
              description: 'A Cinder volume is in an error state.',
            },
          },
        ],
      },
      {
        name: 'neutron',
        rules: [
          {
            alert: 'NeutronAgentDisabled',
            expr: 'neutron:agent:state{adminState!="enabled"} > 0',
            'for': '24h',
            labels: {
              severity: 'SEV-3',
            },
            annotations: {
              summary: 'Neutron agent disabled',
              description: 'A Neutron agent has been administratively disabled for more than 24 hours.',
            },
          },
          {
            alert: 'NeutronAgentDown',
            expr: 'neutron:agent:state != 1',
            'for': '15m',
            labels: {
              severity: 'SEV-2',
            },
            annotations: {
              summary: 'Neutron agent down',
              description: 'A Neutron agent has been down for more than 15 minutes.',
            },
          },
          {
            alert: 'NeutronAgentGroupDown',
            expr: 'min by (exported_service) (neutron:agent:state) == 0',
            'for': '5m',
            labels: {
              severity: 'SEV-1',
            },
            annotations: {
              summary: 'Neutron agent group down',
              description: 'All instances of a specific Neutron agent have been down for more than 5 minutes.',
            },
          }

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
            alert: 'NovaServiceDisabled',
            expr: 'nova:service:state{adminState!="enabled"} > 0',
            'for': '24h',
            labels: {
              severity: 'SEV-3',
            },
            annotations: {
              summary: 'Nova service disabled',
              description: 'A Nova service has been administratively disabled for more than 24 hours.',
            },
          },
          {
            alert: 'NovaServiceDown',
            expr: 'nova:service:state != 1',
            'for': '15m',
            labels: {
              severity: 'SEV-2',
            },
            annotations: {
              summary: 'Nova service down',
              description: 'A Nova service has been down for more than 15 minutes.',
            },
          },
          {
            alert: 'NovaServiceGroupDown',
            expr: 'min by (exported_service) (nova:service:state) == 0',
            'for': '5m',
            labels: {
              severity: 'SEV-1',
            },
            annotations: {
              summary: 'Nova service group down',
              description: 'All instances of a specific Nova service have been down for more than 5 minutes.',
            },
          },
          {
            alert: 'NovaInstanceError',
            expr: 'nova:server:error > 0',
            'for': '24h',
            labels: {
              severity: 'SEV-3',
            },
            annotations: {
              summary: 'Nova server error',
              description: 'A Nova server is in an error state.',
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
}
