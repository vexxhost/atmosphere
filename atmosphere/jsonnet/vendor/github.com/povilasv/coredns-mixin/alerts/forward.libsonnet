{
  _config+:: {
    corednsSelector: error 'must provide selector for coredns',
    corednsForwardLatencyCriticalSeconds: 4,
  },
  prometheusAlerts+:: {
    groups+: [
      {
        name: 'coredns_forward',
        rules: [
          {
            alert: 'CoreDNSForwardLatencyHigh',
            expr: |||
              histogram_quantile(0.99, sum(rate(coredns_forward_request_duration_seconds_bucket{%(corednsSelector)s}[5m])) by(to, le)) > %(corednsForwardLatencyCriticalSeconds)s
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'critical',
            },
            annotations: {
              message: 'CoreDNS has 99th percentile latency of {{ $value }} seconds forwarding requests to {{ $labels.to }}.',
            },
          },
          {
            alert: 'CoreDNSForwardErrorsHigh',
            expr: |||
              sum(rate(coredns_forward_responses_total{%(corednsSelector)s,rcode="SERVFAIL"}[5m]))
                /
              sum(rate(coredns_forward_responses_total{%(corednsSelector)s}[5m])) > 0.03
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'critical',
            },
            annotations: {
              message: 'CoreDNS is returning SERVFAIL for {{ $value | humanizePercentage }} of forward requests to {{ $labels.to }}.',
            },
          },
          {
            alert: 'CoreDNSForwardErrorsHigh',
            expr: |||
              sum(rate(coredns_forward_responses_total{%(corednsSelector)s,rcode="SERVFAIL"}[5m]))
                /
              sum(rate(coredns_forward_responses_total{%(corednsSelector)s}[5m])) > 0.01
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'warning',
            },
            annotations: {
              message: 'CoreDNS is returning SERVFAIL for {{ $value | humanizePercentage }} of forward requests to {{ $labels.to }}.',
            },
          },
          {
            alert: 'CoreDNSForwardHealthcheckFailureCount',
            expr: |||
              sum(rate(coredns_forward_healthcheck_failures_total{%(corednsSelector)s}[5m])) by (to) > 0
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'warning',
            },
            annotations: {
              message: 'CoreDNS health checks have failed to upstream server {{ $labels.to }}.',
            },
          },
          {
            alert: 'CoreDNSForwardHealthcheckBrokenCount',
            expr: |||
              sum(rate(coredns_forward_healthcheck_broken_total{%(corednsSelector)s}[5m])) > 0
            ||| % $._config,
            'for': '10m',
            labels: {
              severity: 'warning',
            },
            annotations: {
              message: 'CoreDNS health checks have failed for all upstream servers.',
            },
          },
        ],
      },
    ],
  },
}
