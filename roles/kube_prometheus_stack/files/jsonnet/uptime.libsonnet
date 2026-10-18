{
  prometheusAlerts+: {
    groups+: [
      {
        name: 'node-uptime',
        rules: [
          {
            alert: 'NodeUptimeExceeded',
            expr: |||
              (
                node_time_seconds{job="node-exporter"}
                - node_boot_time_seconds{job="node-exporter"}
              ) / 86400 > 180
              and
              (
                node_time_seconds{job="node-exporter"}
                - node_boot_time_seconds{job="node-exporter"}
              ) / 86400 <= 365
            |||,
            'for': '1h',
            labels: { severity: 'P4' },
            annotations: {
              summary: 'Node uptime: planned maintenance is overdue',
              description: 'Node {{ $labels.instance }} uptime calculated from node_boot_time_seconds is {{ printf "%.0f" $value }} days, above the 180-day maintenance threshold. Normal operation is below 180 days between planned reboots. Schedule maintenance before uptime exceeds 365 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nodeuptimeexceeded',
            },
          },
          {
            alert: 'NodeUptimeExceeded',
            expr: |||
              (
                node_time_seconds{job="node-exporter"}
                - node_boot_time_seconds{job="node-exporter"}
              ) / 86400 > 365
            |||,
            'for': '30m',
            labels: { severity: 'P3' },
            annotations: {
              summary: 'Node uptime: planned maintenance is overdue',
              description: 'Node {{ $labels.instance }} uptime calculated from node_boot_time_seconds is {{ printf "%.0f" $value }} days, above the 365-day maintenance threshold. Normal operation is below 180 days between planned reboots. Schedule a maintenance window to reboot the node.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nodeuptimeexceeded',
            },
          },
        ],
      },
    ],
  },
}
