{
  prometheusRules+:: {
    groups: [
      {
        name: 'recording',
        rules:
          [
            {
              record: 'nova:build_requests:sum',
              expr: 'sum(openstack_nova_api_build_request)',
            },
          ],
      },
    ],
  },
  prometheusAlerts+: {
    groups+: [
      {
        name: 'cinder',
        rules: [
          {
            alert: 'CinderAgentDisabled',
            expr: 'openstack_cinder_agent_state{adminState!="enabled"} > 0',
            'for': '24h',
            labels: {
              severity: 'P5',
            },
            annotations: {
              summary: 'Cinder agent disabled',
              description: 'A Cinder agent has been administratively disabled for more than 24 hours.',
            },
          },
          {
            alert: 'CinderAgentDown',
            expr: 'openstack_cinder_agent_state != 1',
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Cinder agent down',
              description: 'A Cinder agent has been down for more than 15 minutes.',
            },
          },
          {
            alert: 'CinderAgentGroupDown',
            expr: 'min by (exported_service) (openstack_cinder_agent_state) == 0',
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'Cinder agent group down',
              description: 'All instances of a specific Cinder agent have been down for more than 5 minutes.',
            },
          },
          {
            alert: 'CinderVolumeError',
            expr: 'openstack_cinder_volume_status{status=~"error.*"} > 0',
            'for': '24h',
            labels: {
              severity: 'P4',
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
        rules:
          [
            {
              alert: 'NeutronAgentDisabled',
              expr: 'openstack_neutron_agent_state{adminState!="up"} > 0',
              'for': '24h',
              labels: {
                severity: 'P5',
              },
              annotations: {
                summary: 'Neutron agent disabled',
                description: 'A Neutron agent has been administratively disabled for more than 24 hours.',
              },
            },
            {
              alert: 'NeutronAgentDown',
              expr: 'openstack_neutron_agent_state != 1',
              'for': '15m',
              labels: {
                severity: 'P3',
              },
              annotations: {
                summary: 'Neutron agent down',
                description: 'A Neutron agent has been down for more than 15 minutes.',
              },
            },
            {
              alert: 'NeutronAgentGroupDown',
              expr: 'min by (exported_service) (openstack_neutron_agent_state) == 0',
              'for': '5m',
              labels: {
                severity: 'P2',
              },
              annotations: {
                summary: 'Neutron agent group down',
                description: 'All instances of a specific Neutron agent have been down for more than 5 minutes.',
              },
            }
            {
              alert: 'NeutronNetworkOutOfIPs',
              annotations: {
                description: 'The network {{ $labels.network_id }} is currently at {{ $value }}% utilization.  If the IP addresses run out, it will impact the provisioning of new ports.',
                summary: '[{{ $labels.network_id }}] Network running out of IPs',
              },
              expr: '(sum by (network_id) (openstack_neutron_network_ip_availabilities_used{project_id!=""}) and on (network_id) label_replace(openstack_neutron_network{is_external="true", is_shared="true"}, "network_id", "$1", "id", "(.*)")) / (sum by (network_id) (openstack_neutron_network_ip_availabilities_total{project_id!=""}) and on (network_id) label_replace(openstack_neutron_network{is_external="true", is_shared="true"}, "network_id", "$1", "id", "(.*)")) * 100 > 80',
              'for': '6h',
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'NeutronRouterMultipleActiveL3Agents',
              annotations: {
                summary: 'Neutron HA router has multiple active L3 agents',
                description: 'The router with ID {{ $labels.router_id }} has {{ $value }} L3 agents in active state which can cause network resets and traffic drops.',
              },
              expr: 'sum by (router_id) (openstack_neutron_l3_agent_of_router{ha_state="active"}) > 1',
              'for': '5m',
              labels: {
                severity: 'P3',
              },
            },
          ],
      },
      {
        name: 'neutron-port-bindings',
        rules:
          local alert(severity, expr, description) = {
            alert: 'NeutronPortBindingFailed',
            expr: expr,
            'for': '5m',
            labels: {
              severity: severity,
            },
            annotations: {
              summary: 'Neutron Port Binding Failed',
              description: description,
            },
          };
          [
            alert('P4', 'count(neutron_port{binding_vif_type="binding_failed"}) > 0', 'At least one Neutron port has failed to bind.'),
            alert('P3', '(count(neutron_port{binding_vif_type="binding_failed"}) / count(neutron_port)) > 0.05', 'More than 5% of Neutron ports have failed to bind.'),
            alert('P2', '(count(neutron_port{binding_vif_type="binding_failed"}) / count(neutron_port)) > 0.5', 'More than 50% of Neutron ports have failed to bind.'),
          ],
      },
      {
        name: 'nova',
        rules: [
          {
            alert: 'NovaServiceDisabled',
            expr: 'openstack_nova_agent_state{adminState!="enabled"} > 0',
            'for': '24h',
            labels: {
              severity: 'P5',
            },
            annotations: {
              summary: 'Nova service disabled',
              description: 'A Nova service has been administratively disabled for more than 24 hours.',
            },
          },
          {
            alert: 'NovaServiceDown',
            expr: 'openstack_nova_agent_state != 1',
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Nova service down',
              description: 'A Nova service has been down for more than 15 minutes.',
            },
          },
          {
            alert: 'NovaServiceGroupDown',
            expr: 'sum by (exported_service) (openstack_nova_agent_state) == 0',
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'Nova service group down',
              description: 'All instances of a specific Nova service have been down for more than 5 minutes.',
            },
          },
          {
            alert: 'NovaServerTaskStateStuck',
            annotations: {
              summary: 'Nova server stuck in task state',
              description: 'Nova server with ID {{ $labels.id }} stuck in {{ $labels.task_state }} state for more than 1 hour',
            },
            expr: 'openstack_nova_server_task_state > 0',
            'for': '1h',
            labels: {
              severity: 'P3',
            },
          },
          {
            alert: 'NovaInstanceError',
            expr: 'openstack_nova_server_status{status="ERROR"} > 0',
            'for': '24h',
            labels: {
              severity: 'P4',
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
            expr: 'sum (     openstack_nova_memory_used_bytes   + on(hostname) group_left(adminState)     (0 * openstack_nova_agent_state{exported_service="nova-compute",adminState="enabled"}) ) / sum (     openstack_nova_memory_available_bytes*0.90   + on(hostname) group_left(adminState)     (0 * openstack_nova_agent_state{exported_service="nova-compute",adminState="enabled"}) ) * 100 > 75',
            'for': '6h',
            labels: {
              severity: 'warning',
            },
          },
        ],
      },
      {
        name: 'nova-build-requests',
        rules: [
          {
            alert: 'NovaStuckBuildRequest',
            annotations: {
              summary: 'Nova build request stuck in queue for more than 1 hour',
              description: 'Instance ID {{ $labels.instance_uuid }} (project: {{ $labels.project_id }}) has been stuck in build request state for more than 1 hour.',
            },
            expr: 'openstack_nova_api_build_request > 0',
            'for': '1h',
            labels: {
              severity: 'P4',
            },
          },
          {
            alert: 'NovaStuckBuildRequestIncreasing',
            annotations: {
              summary: 'Nova build request is increasing',
              description: 'Build request count rate is increasing across the cluster.',
            },
            expr: 'rate(nova:build_requests:sum[5m]) > 0',
            'for': '15m',
            labels: {
              severity: 'P3',
            },
          },
        ],
      },
      {
        name: 'octavia',
        rules:
          [
            {
              alert: 'OctaviaLoadBalancerMultipleMaster',
              annotations: {
                summary: 'Octavia load balancer has multiple MASTER Amphorae',
                description: 'Load balancer with ID {{ $labels.loadbalancer_id }} has multiple MASTER Amphorae for more then 15 minutes.',
              },
              expr: 'count by(loadbalancer_id) (openstack_loadbalancer_amphora_status{role="MASTER"}) > 1',
              'for': '15m',
              labels: {
                severity: 'P3',
              },
            },
            {
              alert: 'OctaviaLoadBalancerNotActive',
              annotations: {
                summary: 'Octavia load balancer not active',
                description: 'Load balancer with ID {{ $labels.id }} stuck in non-active state for more then 15 minutes.',
              },
              expr: 'count by (id,name) (openstack_loadbalancer_loadbalancer_status{provisioning_status!="ACTIVE"}) > 0',
              'for': '15m',
              labels: {
                severity: 'P3',
              },
            },
            {
              alert: 'OctaviaAmphoraError',
              annotations: {
                summary: 'Octavia Amphora in error state',
                description: 'Amphora with ID {{ $labels.id }} stuck in error state for more then 15 minutes.',
              },
              expr: 'count by (id,name) (openstack_loadbalancer_amphora_status{status="ERROR"}) > 0',
              'for': '15m',
              labels: {
                severity: 'P3',
              },
            },
            {
              alert: 'OctaviaAmphoraNotOperational',
              annotations: {
                summary: 'Octavia Amphora not operational',
                description: 'Amphora with ID {{ $labels.id }} stuck in non-operational state for more then 1 hour.',
              },
              expr: 'count by (id,name) (openstack_loadbalancer_amphora_status{status!~"READY|ALLOCATED|DELETED"}) > 0',
              'for': '1h',
              labels: {
                severity: 'P3',
              },
            },
          ],
      },
    ],
  },
}
