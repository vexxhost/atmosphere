{
  prometheusAlerts+: {
    groups+: [
      {
        name: 'smartctl-health',
        rules: [
          {
            alert: 'SmartctlDiskUnhealthy',
            expr: 'smartctl_device_smart_status == 0',
            'for': '2m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'Disk: SMART health check failed',
              description: 'The disk {{ $labels.device }} (model: {{ $labels.model_name }}) on node {{ $labels.instance }} has failed its SMART health self-assessment test. This indicates imminent disk failure and the disk should be replaced immediately.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskunhealthy',
            },
          },
          {
            alert: 'SmartctlDiskWearoutCritical',
            expr: 'smartctl_device_percentage_used > 90',
            'for': '5m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Disk: wear level critical',
              description: 'The disk {{ $labels.device }} (model: {{ $labels.model_name }}) on node {{ $labels.instance }} has {{ $value }}% wear. The disk has exceeded 90% of its rated endurance and should be replaced soon to avoid data loss.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskwearoutcritical',
            },
          },
          {
            alert: 'SmartctlDiskWearoutWarning',
            expr: 'smartctl_device_percentage_used > 75 and smartctl_device_percentage_used <= 90',
            'for': '15m',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Disk: wear level elevated',
              description: 'The disk {{ $labels.device }} (model: {{ $labels.model_name }}) on node {{ $labels.instance }} has {{ $value }}% wear. The disk has exceeded 75% of its rated endurance. Plan a replacement during the next maintenance window.',
            },
          },
          {
            alert: 'SmartctlDiskTemperatureHigh',
            expr: 'smartctl_device_temperature{temperature_type="current"} > 60',
            'for': '15m',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Disk: temperature high',
              description: 'The disk {{ $labels.device }} (model: {{ $labels.model_name }}) on node {{ $labels.instance }} has a temperature of {{ $value }}°C, which exceeds the 60°C threshold. Normal operating temperature is below 45°C. Check cooling and airflow.',
            },
          },
          {
            alert: 'SmartctlDiskReallocatedSectors',
            expr: 'smartctl_device_smart_attribute{smart_attribute_name="Reallocated_Sector_Ct", smart_attribute_type="raw"} > 0',
            'for': '5m',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Disk: reallocated sectors detected',
              description: 'The disk {{ $labels.device }} (model: {{ $labels.model_name }}) on node {{ $labels.instance }} has {{ $value }} reallocated sectors. This indicates the disk has remapped bad sectors to spare areas. Monitor the trend and plan replacement if the count increases.',
            },
          },
        ],
      },
      {
        name: 'smartctl-exporter',
        rules: [
          {
            alert: 'SmartctlExporterDown',
            expr: 'up{job="smartctl"} == 0',
            'for': '15m',
            labels: {
              severity: 'P5',
            },
            annotations: {
              summary: 'smartctl exporter: unreachable',
              description: 'The smartctl exporter on node {{ $labels.instance }} has been unreachable for more than 15 minutes. Disk health monitoring is unavailable for this node.',
            },
          },
        ],
      },
    ],
  },
}
