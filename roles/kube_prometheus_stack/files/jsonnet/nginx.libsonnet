{
  prometheusAlerts+: {
    groups+: [
      {
        name: 'nginx-ingress',
        rules: [
          {
            alert: 'NginxIngressHighErrorRate',
            expr: |||
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[5m]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[5m]))
              ) > 0.05
            |||,
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'NGINX Ingress: elevated error rate affecting service',
              description: 'The service {{ $labels.service }} is returning 5xx errors at {{ $value | humanizePercentage }} over the last 5 minutes, which exceeds the threshold of 5%. Normal operation expects error rates below 1%.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresshigherrorrate',
            },
          },
          {
            alert: 'NginxIngressCriticalErrorRate',
            expr: |||
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[5m]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[5m]))
              ) > 0.20
            |||,
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'NGINX Ingress: critical error rate affecting service availability',
              description: 'The service {{ $labels.service }} is returning 5xx errors at {{ $value | humanizePercentage }} over the last 5 minutes, which exceeds the critical threshold of 20%. This indicates a severe service degradation.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresscriticalerrorrate',
            },
          },
        ],
      },
    ],
  },
}
