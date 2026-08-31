local activeNodes = |||
  label_replace(
    openstack_ironic_node{provision_state="active"} == 1,
    "node_uuid", "$1", "id", "(.+)"
  )
|||;

local activeNodesForThirtyMinutes = |||
  (
    label_replace(
      count_over_time(openstack_ironic_node{provision_state="active"}[30m]) >= 20,
      "node_uuid", "$1", "id", "(.+)"
    )
  ) and on (node_uuid) (
    label_replace(
      openstack_ironic_node{provision_state="active"} == 1,
      "node_uuid", "$1", "id", "(.+)"
    )
  )
|||;

local activeSensorStatus(metric, value) =
  'max by (node_uuid, node_name, instance_uuid, sensor_id) (' + metric + ' == ' + std.toString(value) + ') '
  + 'and on (node_uuid) (' + activeNodes + ')';

{
  prometheusRules+:: {
    groups: [
      {
        name: 'ironic-sensor-recording',
        rules: [
          {
            record: 'openstack:ironic_active_sensor_nodes:count',
            expr: 'count(count by (node_uuid) (baremetal_last_payload_timestamp_seconds) and on (node_uuid) (' + activeNodes + '))',
          },
        ],
      },
    ],
  },
  prometheusAlerts+:: {
    groups: [
      {
        name: 'ironic-sensors',
        rules: [
          {
            alert: 'IronicSensorPayloadStale',
            expr: '(' + activeNodesForThirtyMinutes + ') unless on (node_uuid) (baremetal_last_payload_timestamp_seconds > time() - 1800)',
            'for': '10m',
            labels: { severity: 'P4' },
            annotations: {
              summary: 'Active Ironic node sensor payload is stale',
              description: 'Active Ironic node {{ $labels.name }} ({{ $labels.id }}) has had no fresh hardware sensor payload for at least 30 minutes.',
            },
          },
          {
            alert: 'IronicActiveNodeTemperatureCritical',
            expr: activeSensorStatus('baremetal_temperature_status', 2),
            'for': '5m',
            labels: { severity: 'P3' },
            annotations: {
              summary: 'Active Ironic node temperature is critical',
              description: 'Temperature sensor {{ $labels.sensor_id }} on active Ironic node {{ $labels.node_name }} ({{ $labels.node_uuid }}) is critical.',
            },
          },
          {
            alert: 'IronicActiveNodePowerCritical',
            expr: activeSensorStatus('baremetal_power_status', 2),
            'for': '5m',
            labels: { severity: 'P3' },
            annotations: {
              summary: 'Active Ironic node power sensor is critical',
              description: 'Power sensor {{ $labels.sensor_id }} on active Ironic node {{ $labels.node_name }} ({{ $labels.node_uuid }}) is critical.',
            },
          },
          {
            alert: 'IronicActiveNodeFanCritical',
            expr: activeSensorStatus('baremetal_fan_status', 2),
            'for': '5m',
            labels: { severity: 'P3' },
            annotations: {
              summary: 'Active Ironic node fan is critical',
              description: 'Fan sensor {{ $labels.sensor_id }} on active Ironic node {{ $labels.node_name }} ({{ $labels.node_uuid }}) is critical.',
            },
          },
          {
            alert: 'IronicActiveNodeDriveCritical',
            expr: activeSensorStatus('baremetal_drive_status', 2),
            'for': '5m',
            labels: { severity: 'P4' },
            annotations: {
              summary: 'Active Ironic node drive is critical',
              description: 'Drive sensor {{ $labels.sensor_id }} on active Ironic node {{ $labels.node_name }} ({{ $labels.node_uuid }}) is critical.',
            },
          },
          {
            alert: 'IronicActiveNodeHardwareWarning',
            expr: activeSensorStatus('{__name__=~"baremetal_(temperature|power|fan|drive)_status"}', 1),
            'for': '15m',
            labels: { severity: 'P5' },
            annotations: {
              summary: 'Active Ironic node hardware sensor reports a warning',
              description: 'Hardware sensor {{ $labels.sensor_id }} on active Ironic node {{ $labels.node_name }} ({{ $labels.node_uuid }}) has reported a warning for 15 minutes.',
            },
          },
        ],
      },
    ],
  },
}
