local burnRateTiers = import 'burnrate.libsonnet';

local errorRatio(window) = |||
  sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[%(window)s]))
  /
  sum by (service) (rate(nginx_ingress_controller_requests[%(window)s]))
||| % { window: window };

local burnRateExpr(tier) = |||
  (
  %(longRatio)s) > %(threshold)s
  and
  (
  %(shortRatio)s) > %(threshold)s
  and
  sum by (service) (rate(nginx_ingress_controller_requests[%(shortWindow)s])) > 1
||| % {
  longRatio: errorRatio(tier.longWindow),
  shortRatio: errorRatio(tier.shortWindow),
  threshold: tier.threshold,
  shortWindow: tier.shortWindow,
};

{
  prometheusAlerts+: {
    groups+: [
      {
        name: 'nginx-ingress',
        rules: [
          {
            alert: 'NginxIngressCriticalErrorBudgetBurn',
            expr: burnRateExpr(burnRateTiers.critical),
            'for': '2m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'NGINX Ingress: elevated 5xx errors rapidly consuming error budget',
              description: 'The service {{ $labels.service }} error rate is {{ $value | humanizePercentage }} over the last hour, which exceeds the 1.44% burn-rate threshold (14.4x against 99.9% SLO). At this rate, the 30-day error budget exhausts in under 2.1 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresscriticalerrorbudgetburn',
            },
          },
          {
            alert: 'NginxIngressHighErrorBudgetBurn',
            expr: burnRateExpr(burnRateTiers.high),
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'NGINX Ingress: sustained 5xx errors depleting error budget',
              description: 'The service {{ $labels.service }} error rate is {{ $value | humanizePercentage }} over the last 6 hours, which exceeds the 0.6% burn-rate threshold (6x against 99.9% SLO). At this rate, the 30-day error budget exhausts in under 5 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresshigherrorbudgetburn',
            },
          },
          {
            alert: 'NginxIngressModerateErrorBudgetBurn',
            expr: burnRateExpr(burnRateTiers.moderate),
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'NGINX Ingress: ongoing 5xx errors steadily consuming error budget',
              description: 'The service {{ $labels.service }} error rate is {{ $value | humanizePercentage }} over the last day, which exceeds the 0.3% burn-rate threshold (3x against 99.9% SLO). At this rate, the 30-day error budget exhausts in under 10 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingressmoderateerrorbudgetburn',
            },
          },
          {
            alert: 'NginxIngressLowErrorBudgetBurn',
            expr: burnRateExpr(burnRateTiers.low),
            'for': '1h',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'NGINX Ingress: low-level 5xx errors eroding error budget',
              description: 'The service {{ $labels.service }} error rate is {{ $value | humanizePercentage }} over the last 3 days, which exceeds the 0.1% burn-rate threshold (1x against 99.9% SLO). At this rate, the 30-day error budget exhausts before the window resets.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresslowerrorbudgetburn',
            },
          },
          {
            alert: 'NginxIngressTLSCertificateExpiringSoon',
            expr: |||
              (nginx_ingress_controller_ssl_expire_time_seconds{secret_name!=""} - time() < 21 * 24 * 3600)
              and
              (nginx_ingress_controller_ssl_expire_time_seconds{secret_name!=""} - time() >= 7 * 24 * 3600)
            |||,
            'for': '1h',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'NGINX Ingress TLS: certificate for {{ $labels.host }} expires within 21 days',
              description: 'The certificate serving {{ $labels.host }} has {{ $value | humanizeDuration }} remaining, below the 21-day warning threshold. It should renew automatically via cert-manager; normal behavior is renewal before expiry.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresstlscertificateexpiringsoon',
            },
          },
          {
            alert: 'NginxIngressTLSCertificateExpiringCritical',
            expr: |||
              nginx_ingress_controller_ssl_expire_time_seconds{secret_name!=""} - time() < 7 * 24 * 3600
            |||,
            'for': '1h',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'NGINX Ingress TLS: certificate for {{ $labels.host }} expires within 7 days',
              description: 'The certificate serving {{ $labels.host }} has {{ $value | humanizeDuration }} remaining, below the 7-day critical threshold. Check cert-manager and renew or replace the certificate before it expires; normal behavior is renewal before expiry.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresstlscertificateexpiringcritical',
            },
          },
        ],
      },
    ],
  },
}
