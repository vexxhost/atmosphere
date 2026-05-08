{
  prometheusAlerts+: {
    groups: [
      {
        name: 'geneve',
        rules: [
          {
            alert: 'GeneveTransmitErrors',
            expr: |||
              (
                rate(node_network_transmit_errs_total{job="node-exporter"}[5m])
                * on(instance, device) group_left(driver)
                node_ethtool_info{job="node-exporter", driver="geneve"}
              ) > 1.67
            |||,
            'for': '15m',
            labels: { severity: 'warning' },
            annotations: {
              summary: 'Geneve overlay: transmit failures may affect tenant traffic on a compute host',
              description: '{{ $labels.instance }} interface {{ $labels.device }} has averaged {{ printf "%.2f" $value }} transmit errors per second over the last 5 minutes (threshold > 1.67/s, ~100/min). Normal behavior is zero sustained transmit errors on Geneve tunnel interfaces.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#genevetransmiterrors',
            },
          },
        ],
      },
    ],
  },
}
