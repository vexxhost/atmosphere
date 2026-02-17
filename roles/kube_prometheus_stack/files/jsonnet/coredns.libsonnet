local burnRateTiers = import 'burnrate.libsonnet';

local errorRatio(window) = |||
  sum(rate(coredns_dns_responses_total{job="coredns",rcode="SERVFAIL"}[%(window)s]))
  /
  sum(rate(coredns_dns_responses_total{job="coredns"}[%(window)s]))
||| % { window: window };

local burnRateExpr(tier) = |||
  (
  %(longRatio)s) > %(threshold)s
  and
  (
  %(shortRatio)s) > %(threshold)s
  and
  sum(rate(coredns_dns_responses_total{job="coredns"}[%(shortWindow)s])) > 1
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
        name: 'coredns',
        rules: [
          {
            alert: 'CoreDNSCriticalErrorBudgetBurn',
            expr: burnRateExpr(burnRateTiers.critical),
            'for': '2m',
            labels: {
              severity: 'P1',
            },
            annotations: {
              summary: 'CoreDNS: SERVFAIL rate rapidly consuming error budget',
              description: 'The CoreDNS SERVFAIL rate is {{ $value | humanizePercentage }} over the last hour, which exceeds the 1.44% burn-rate threshold (14.4x against 99.9% SLO). At this rate, the 30-day error budget exhausts in under 2.1 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#corednscriticalerrorbudgetburn',
            },
          },
          {
            alert: 'CoreDNSHighErrorBudgetBurn',
            expr: burnRateExpr(burnRateTiers.high),
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'CoreDNS: sustained SERVFAIL rate depleting error budget',
              description: 'The CoreDNS SERVFAIL rate is {{ $value | humanizePercentage }} over the last 6 hours, which exceeds the 0.6% burn-rate threshold (6x against 99.9% SLO). At this rate, the 30-day error budget exhausts in under 5 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#corednshigherrorbudgetburn',
            },
          },
          {
            alert: 'CoreDNSModerateErrorBudgetBurn',
            expr: burnRateExpr(burnRateTiers.moderate),
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'CoreDNS: ongoing SERVFAIL rate steadily consuming error budget',
              description: 'The CoreDNS SERVFAIL rate is {{ $value | humanizePercentage }} over the last day, which exceeds the 0.3% burn-rate threshold (3x against 99.9% SLO). At this rate, the 30-day error budget exhausts in under 10 days.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#corednsmoderateerrorbudgetburn',
            },
          },
          {
            alert: 'CoreDNSLowErrorBudgetBurn',
            expr: burnRateExpr(burnRateTiers.low),
            'for': '1h',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'CoreDNS: low-level SERVFAIL rate eroding error budget',
              description: 'The CoreDNS SERVFAIL rate is {{ $value | humanizePercentage }} over the last 3 days, which exceeds the 0.1% burn-rate threshold (1x against 99.9% SLO). At this rate, the 30-day error budget exhausts before the window resets.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#corednslowerrorbudgetburn',
            },
          },
          {
            alert: 'CoreDNSDown',
            expr: 'absent(up{job="coredns"} == 1)',
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'CoreDNS: instance has disappeared from Prometheus target discovery',
              description: 'CoreDNS has disappeared from Prometheus target discovery for more than 15 minutes. This could indicate a crashed CoreDNS pod or a misconfigured scrape target.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#corednsdown',
            },
          },
        ],
      },
    ],
  },
}
