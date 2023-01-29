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
              message: 'CoreDNS has disappeared from Prometheus target discovery.',
            },
          },
          {
            alert: 'CoreDNSLatencyHigh',
            expr: |||
              histogram_quantile(0.99, sum(rate(coredns_dns_request_duration_seconds_bucket{%(corednsSelector)s}[5m])) by(server, zone, le)) > %(corednsLatencyCriticalSeconds)s
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'critical',
            },
            annotations: {
              message: 'CoreDNS has 99th percentile latency of {{ $value }} seconds for server {{ $labels.server }} zone {{ $labels.zone }} .',
            },
          },
          {
            alert: 'CoreDNSErrorsHigh',
            expr: |||
              sum(rate(coredns_dns_responses_total{%(corednsSelector)s,rcode="SERVFAIL"}[5m]))
                /
              sum(rate(coredns_dns_responses_total{%(corednsSelector)s}[5m])) > 0.03
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'critical',
            },
            annotations: {
              message: 'CoreDNS is returning SERVFAIL for {{ $value | humanizePercentage }} of requests.',
            },
          },
          {
            alert: 'CoreDNSErrorsHigh',
            expr: |||
              sum(rate(coredns_dns_responses_total{%(corednsSelector)s,rcode="SERVFAIL"}[5m]))
                /
              sum(rate(coredns_dns_responses_total{%(corednsSelector)s}[5m])) > 0.01
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'warning',
            },
            annotations: {
              message: 'CoreDNS is returning SERVFAIL for {{ $value | humanizePercentage }} of requests.',
            },
          },
        ],
      },
    ],
  },
}
