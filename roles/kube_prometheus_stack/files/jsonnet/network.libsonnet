{
  prometheusAlerts+: {
    groups: [
      {
        name: 'network',
        rules: [
          {
            alert: 'NodeNetworkMulticast',
            expr: 'rate(node_network_receive_multicast_total{job="node-exporter"}[5m]) > 1000',
            'for': '24h',
            labels: {
              severity: 'P5',
            },
            annotations: {
              summary: 'Node network: sustained multicast or broadcast traffic is increasing packet-processing load',
              description: '{{ $labels.instance }} interface {{ $labels.device }} has received {{ printf "%.2f" $value }} multicast or broadcast packets per second over the last 5 minutes, above the 1,000 packets per second capacity-planning threshold for 24 hours. Normal behavior is below 1,000 packets per second or limited to short bursts.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nodenetworkmulticast',
            },
          },
        ],
      },
    ],
  },
}
