local burnRateTiers = import 'burnrate.libsonnet';

local errorRatio(window) = |||
  sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[%(window)s]))
  /
  sum by (service) (rate(nginx_ingress_controller_requests[%(window)s]))
||| % { window: window };

// NOTE: Every ingress-nginx controller pod reports every certificate, once per
//       host. Taking the earliest expiry per Secret produces a single alert for
//       a certificate shared by many hosts (such as a wildcard certificate) and
//       still catches a controller that serves an older copy. Certificates
//       without a Secret (the controller's default certificate) are excluded.
local certificateExpiryExpr(days) = |||
  min by (namespace, secret_name) (
    nginx_ingress_controller_ssl_expire_time_seconds{secret_name!=""}
  ) - time() < %(days)d * 24 * 3600
||| % { days: days };

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
            // NOTE: This alert keeps firing below 7 days so there is no gap
            //       while the P2 alert is pending. Alertmanager inhibits it
            //       once NginxIngressTLSCertificateExpiringCritical fires.
            expr: certificateExpiryExpr(21),
            'for': '1h',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'NGINX Ingress TLS: certificate expires within 21 days',
              description: 'The TLS certificate in Secret {{ $labels.namespace }}/{{ $labels.secret_name }} served by NGINX Ingress expires in {{ $value | humanizeDuration }}, which is below the 21-day warning threshold. cert-manager renews certificates when a third of their lifetime remains (30 days for a 90-day certificate), so renewal has stalled or the certificate is managed manually. Normal behavior is more than 21 days remaining.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresstlscertificateexpiringsoon',
            },
          },
          {
            alert: 'NginxIngressTLSCertificateExpiringCritical',
            expr: certificateExpiryExpr(7),
            'for': '1h',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'NGINX Ingress TLS: certificate expires within 7 days and will break HTTPS for its hosts',
              description: 'The TLS certificate in Secret {{ $labels.namespace }}/{{ $labels.secret_name }} served by NGINX Ingress expires in {{ $value | humanizeDuration }}, which is below the 7-day critical threshold. Every host using this Secret fails TLS verification once it expires. Normal behavior is more than 21 days remaining.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#nginxingresstlscertificateexpiringcritical',
            },
          },
        ],
      },
    ],
  },
}
