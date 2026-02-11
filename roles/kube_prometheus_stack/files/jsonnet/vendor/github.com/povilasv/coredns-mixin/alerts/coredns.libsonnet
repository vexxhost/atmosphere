{
  _config+:: {
    corednsSelector: error 'must provide selector for coredns',
    corednsLatencyCriticalSeconds: 4,
  },
  prometheusAlerts+:: {
    groups+: [
      {
        name: 'coredns',
        rules: [
          {
            alert: 'CoreDNSDown',
            'for': '15m',
            expr: |||
              absent(up{%(corednsSelector)s} == 1)
            ||| % $._config,
            labels: {
              severity: 'critical',
            },
            annotations: {
              summary: 'CoreDNS has disappeared from Prometheus target discovery.',
              description: 'CoreDNS has disappeared from Prometheus target discovery.',
            },
          },
          {
            alert: 'CoreDNSLatencyHigh',
            expr: |||
              histogram_quantile(0.99, sum(rate(coredns_dns_request_duration_seconds_bucket{%(corednsSelector)s}[5m])) without (instance,pod)) > %(corednsLatencyCriticalSeconds)s
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'critical',
            },
            annotations: {
              summary: 'CoreDNS is experiencing high 99th percentile latency.',
              description: 'CoreDNS has 99th percentile latency of {{ $value }} seconds for server {{ $labels.server }} zone {{ $labels.zone }} .',
            },
          },
          {
            alert: 'CoreDNSErrorsHigh',
            expr: |||
              sum without (pod, instance, server, zone, view, rcode, plugin) (rate(coredns_dns_responses_total{%(corednsSelector)s,rcode="SERVFAIL"}[5m]))
                /
              sum without (pod, instance, server, zone, view, rcode, plugin) (rate(coredns_dns_responses_total{%(corednsSelector)s}[5m])) > 0.03
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'critical',
            },
            annotations: {
              summary: 'CoreDNS is returning SERVFAIL.',
              description: 'CoreDNS is returning SERVFAIL for {{ $value | humanizePercentage }} of requests.',
            },
          },
          {
            alert: 'CoreDNSErrorsHigh',
            expr: |||
              sum without (pod, instance, server, zone, view, rcode, plugin) (rate(coredns_dns_responses_total{%(corednsSelector)s,rcode="SERVFAIL"}[5m]))
                /
              sum without (pod, instance, server, zone, view, rcode, plugin) (rate(coredns_dns_responses_total{%(corednsSelector)s}[5m])) > 0.01
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'warning',
            },
            annotations: {
              summary: 'CoreDNS is returning SERVFAIL.',
              description: 'CoreDNS is returning SERVFAIL for {{ $value | humanizePercentage }} of requests.',
            },
          },
        ],
      },
    ],
  },
}
