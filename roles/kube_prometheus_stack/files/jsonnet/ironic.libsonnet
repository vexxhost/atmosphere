{
  prometheusRules+:: {
    groups: [
      {
        name: 'ironic-recording',
        rules: [
          {
            record: 'openstack:ironic_nodes:count',
            expr: 'sum(openstack_ironic_node)',
          },
          {
            record: 'openstack:ironic_nodes_by_provision_state:count',
            expr: 'sum by (provision_state) (openstack_ironic_node)',
          },
          {
            record: 'openstack:ironic_active_nodes:count',
            expr: 'sum(openstack_ironic_node{provision_state="active"})',
          },
          {
            record: 'openstack:ironic_maintenance_nodes:count',
            expr: 'sum(openstack_ironic_node{maintenance="true"})',
          },
        ],
      },
    ],
  },
  prometheusAlerts+:: {
    groups: [
      {
        name: 'ironic-lifecycle',
        rules: [
          {
            alert: 'IronicAPIUnavailable',
            expr: '(openstack_ironic_up == 0) or absent(openstack_ironic_up)',
            'for': '5m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Ironic API metrics are unavailable',
              description: 'The Ironic API collector has been unavailable for more than 5 minutes.',
            },
          },
          {
            alert: 'IronicNodeProvisioningFailed',
            expr: 'openstack_ironic_node{provision_state=~"deploy failed|error"} == 1',
            'for': '5m',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Ironic node provisioning failed',
              description: 'Ironic node {{ $labels.name }} ({{ $labels.id }}) is in {{ $labels.provision_state }}.',
            },
          },
          {
            alert: 'IronicNodeProvisioningStalled',
            expr: 'openstack_ironic_node{provision_state=~"deploying|wait call-back|deleting"} == 1',
            'for': '2h',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Ironic node provisioning is stalled',
              description: 'Ironic node {{ $labels.name }} ({{ $labels.id }}) has remained in {{ $labels.provision_state }} for more than 2 hours.',
            },
          },
          {
            alert: 'IronicActiveNodePowerStateUnexpected',
            expr: 'openstack_ironic_node{provision_state="active",power_state!="power on"} == 1',
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Active Ironic node has an unexpected power state',
              description: 'Active Ironic node {{ $labels.name }} ({{ $labels.id }}) has reported {{ $labels.power_state }} for more than 15 minutes.',
            },
          },
        ],
      },
    ],
  },
}
