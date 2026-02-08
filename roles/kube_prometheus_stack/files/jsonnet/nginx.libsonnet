{
  prometheusAlerts+: {
    groups+: [
      {
        name: 'nginx-ingress',
        rules: [
          {
            alert: 'NginxIngressCriticalErrorBudgetBurn',
            expr: |||
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[1h]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[1h]))
              ) > 0.0144
              and
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[5m]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[5m]))
              ) > 0.0144
              and
              sum by (service) (rate(nginx_ingress_controller_requests[5m])) > 1
            |||,
            'for': '2m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'NGINX Ingress: critical error budget burn rate',
              description: 'The service {{ $labels.service }} error rate is {{ $value | humanizePercentage }} over the last hour, which exceeds the 1.44% burn-rate threshold (14.4x against 99.9% SLO). At this rate, the 30-day error budget exhausts in under 2.1 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresscriticalerrorbudgetburn',
            },
          },
          {
            alert: 'NginxIngressHighErrorBudgetBurn',
            expr: |||
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[6h]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[6h]))
              ) > 0.006
              and
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[30m]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[30m]))
              ) > 0.006
              and
              sum by (service) (rate(nginx_ingress_controller_requests[30m])) > 1
            |||,
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'NGINX Ingress: high error budget burn rate',
              description: 'The service {{ $labels.service }} error rate is {{ $value | humanizePercentage }} over the last 6 hours, which exceeds the 0.6% burn-rate threshold (6x against 99.9% SLO). At this rate, the 30-day error budget exhausts in under 5 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresshigherrorbudgetburn',
            },
          },
          {
            alert: 'NginxIngressModerateErrorBudgetBurn',
            expr: |||
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[1d]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[1d]))
              ) > 0.003
              and
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[2h]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[2h]))
              ) > 0.003
              and
              sum by (service) (rate(nginx_ingress_controller_requests[2h])) > 1
            |||,
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'NGINX Ingress: moderate error budget burn rate',
              description: 'The service {{ $labels.service }} error rate is {{ $value | humanizePercentage }} over the last day, which exceeds the 0.3% burn-rate threshold (3x against 99.9% SLO). At this rate, the 30-day error budget exhausts in under 10 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingressmoderateerrorbudgetburn',
            },
          },
          {
            alert: 'NginxIngressLowErrorBudgetBurn',
            expr: |||
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[3d]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[3d]))
              ) > 0.001
              and
              (
                sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[6h]))
                /
                sum by (service) (rate(nginx_ingress_controller_requests[6h]))
              ) > 0.001
              and
              sum by (service) (rate(nginx_ingress_controller_requests[6h])) > 1
            |||,
            'for': '1h',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'NGINX Ingress: low error budget burn rate',
              description: 'The service {{ $labels.service }} error rate is {{ $value | humanizePercentage }} over the last 3 days, which exceeds the 0.1% burn-rate threshold (1x against 99.9% SLO). At this rate, the 30-day error budget exhausts before the window resets.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresslowerrorbudgetburn',
            },
          },
        ],
      },
    ],
  },
}
