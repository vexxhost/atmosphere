{
  prometheusAlerts+: {
    groups+: [
      {
        name: 'goldpinger',
        rules: [
          {
            alert: 'GoldpingerHighUnhealthyRatio',
            expr: |||
              (
                sum(goldpinger_nodes_health_total{status="unhealthy"})
                /
                sum(goldpinger_nodes_health_total)
              ) > 0.1
            |||,
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'Goldpinger: high percentage of cluster nodes unhealthy',
              description: 'More than 10% of nodes (current: {{ $value | humanizePercentage }}) are reporting as unhealthy for at least 5 minutes. Normal operation expects 0% unhealthy nodes.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#goldpingerhighunhealthyratio',
            },
          },
          {
            alert: 'GoldpingerNodeUnreachable',
            expr: |||
              (
                count by (host_ip) (
                  histogram_quantile(0.5,
                    sum by (instance, host_ip, le) (
                      rate(goldpinger_peers_response_time_s_bucket{call_type="ping"}[5m])
                    )
                  ) > 1.0
                )
                /
                scalar(count(goldpinger_cluster_health_total))
              ) > 0.5
            |||,
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'Goldpinger: node unreachable by majority of cluster',
              description: 'Node with IP {{ $labels.host_ip }} has a median ping latency above 1s from more than 50% (current: {{ $value | humanizePercentage }}) of Goldpinger instances. Normal operation expects all nodes to be reachable with sub-10ms latency.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#goldpingernodeunreachable',
            },
          },
          {
            alert: 'GoldpingerHighPeerLatency',
            expr: |||
              histogram_quantile(0.95,
                sum by (le) (
                  rate(goldpinger_peers_response_time_s_bucket{call_type="ping"}[5m])
                )
              ) > 0.5
            |||,
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Goldpinger: high cluster-wide peer latency',
              description: 'The 95th percentile of peer-to-peer latency is {{ $value | humanizeDuration }}, which exceeds the threshold of 500ms. Normal latency is typically below 10ms.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#goldpingerhighpeerlatency',
            },
          },
          {
            alert: 'GoldpingerHighErrorRate',
            expr: |||
              (
                sum(rate(goldpinger_errors_total{type="ping"}[5m]))
                /
                sum(rate(goldpinger_stats_total{action="ping",group="made"}[5m]))
              ) > 0.05
            |||,
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Goldpinger: high ping error rate',
              description: 'More than 5% (current: {{ $value | humanizePercentage }}) of Goldpinger ping attempts are failing. Normal operation expects less than 0.1% error rate.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#goldpingerhigherrorrate',
            },
          },
        ],
      },
    ],
  },
}
