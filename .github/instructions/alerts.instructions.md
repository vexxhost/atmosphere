---
applyTo: "roles/kube_prometheus_stack/files/jsonnet/**,roles/kube_prometheus_stack/rules_test.go,doc/source/admin/monitoring.rst"
---

Alerts are managed as a mixture of existing mixins with some additional
modifications to the existing mixins.  It also includes some custom
rules that are not part of the mixins.

## Required Reading

Before writing or modifying any alert, read the following file for the
alerting philosophy, severity level definitions, and notification
routing expectations:

  doc/source/admin/monitoring.rst

All alerts must conform to the philosophy and severity definitions
described there.

## Alert Naming

Alert names must use PascalCase (e.g., `GoldpingerHighUnhealthyRatio`,
`CinderAgentDown`).  The component name should be the prefix, followed
by a concise description of the condition.

## File Structure

Every single component should have its own file in the `jsonnet`
directory, and should be named according to the component it is
alerting on.

Avoid adding comments in the `jsonnet` file but instead aim to have
more productive summaries and descriptions for the alerts, following the
format guidelines below.

## Alert Duration (`for`)

Use best judgement when using `for` to avoid alert fatigue, but also to
ensure that alerts are actionable and not too noisy.  In general, you
should aim for the following:

- P1: A short `for` (e.g., 1-2 minutes) to ensure immediate attention
  while avoiding false pages from transient scrape failures or
  Prometheus restarts.  Never use `for: 0` as a single missed scrape
  can trigger a false alert.
- P2: A short `for` (e.g., 5 minutes) to allow for transient issues to
  resolve themselves while still ensuring timely action.
- P3: A moderate `for` (e.g., 15-30 minutes) to allow for some
  variability in system performance while still ensuring that issues are
  addressed in a reasonable timeframe.
- P4: A longer `for` (e.g., 1 hour) to allow for minor issues to be
  addressed without causing unnecessary alert fatigue.
- P5: A longer `for` (e.g., 24 hours) or no `for` at all, since these
  alerts are informational and do not require immediate action.

## Summary and Description Format

Every alert must have a `summary` and `description` annotation that
follow these conventions:

- **summary**: A concise one-liner that identifies the affected
  component and the user-visible impact.  Format:
  `<Component>: <Impact statement>`
  Example: `API Gateway: elevated error rate affecting client requests`

- **description**: A longer explanation that includes the metric being
  evaluated, the current value using template variables (e.g.,
  `{{ $value }}`), the threshold that was breached, and what normal
  behavior looks like.
  Example: `The API error rate is {{ $value }}% over the last 5 minutes,
  which exceeds the threshold of 1%.  Normal error rate is below 0.1%.`

## Inhibition Rules

When creating alerts that belong to a tiered or graduated set (for
example, multi-window burn-rate alerts like Critical/High/Moderate/Low),
always add Alertmanager inhibition rules so that higher-severity tiers
suppress lower-severity tiers for the same resource.  This prevents
redundant notifications when a faster-burn alert already covers the
incident.

Inhibition rules live in
`roles/kube_prometheus_stack/vars/main.yml` under
`alertmanager.config.inhibit_rules`.

### When to add an inhibition rule

- **Burn-rate tiers**: If a component has multiple burn-rate alerts
  (e.g., Critical, High, Moderate, Low), the faster-burn alert should
  suppress all slower-burn alerts for the same identifying labels
  (e.g., `service`, `namespace`).
- **Parent-child dependencies**: If a parent component failure (e.g.,
  node down) makes a child alert redundant (e.g., pod on that node),
  add an inhibition rule.
- **Same-component escalations**: If a component has both a degraded
  and a down alert, the down alert should suppress the degraded alert.

### Format

```yaml
inhibit_rules:
  - source_matchers:
      - alertname = "ComponentCriticalAlert"
    target_matchers:
      - alertname =~ "Component(High|Moderate|Low)Alert"
    equal:
      - <identifying-label>
```

The `equal` field must list all labels that identify the same resource
instance (e.g., `service`, `namespace`, `instance`).

## Runbook and Documentation Requirements

Every alert must have a corresponding entry in the Alerts Reference
section of:

  doc/source/admin/monitoring.rst

### What to include in the documentation entry

Each alert entry in the rst file must include:

1. The alert name as a definition term (using double backticks),
   preserving the original PascalCase of the alert name.
2. A description of what the alert means and why it fires.
3. The likely root causes.
4. Step-by-step diagnostic and remediation procedures, including any
   relevant commands.

Entries in the Alerts Reference section must be ordered alphabetically
by alert name.

### Runbook URL annotation

Every P1 through P3 alert must include a `runbook_url` annotation
pointing to the rendered documentation anchor for that alert.  The URL
format is:

  https://vexxhost.github.io/atmosphere/admin/monitoring.html#<alert-name-lowercase>

P4 and P5 alerts should include a `runbook_url` where possible.

## Test Requirements

Every new or modified alert must have corresponding test cases in
`roles/kube_prometheus_stack/files/jsonnet/tests.yml`.  Tests are run
via `promtool test rules` through the Go test in
`roles/kube_prometheus_stack/rules_test.go`.

### What to include in tests

Each alert must have at least two test cases:

1. A **negative test** that verifies the alert does NOT fire under
   normal conditions (i.e., `exp_alerts: []`).
2. A **positive test** that verifies the alert DOES fire when the
   threshold is breached.

### Positive test expectations

The `exp_alerts` section must include ALL annotations that the alert
rule produces.  This means `summary`, `description`, and `runbook_url`
(if present) must all be listed in `exp_annotations`.  Omitting any
annotation will cause `promtool test rules` to fail.

### Test data conventions

Use RFC 5737 documentation IP ranges (`192.0.2.0/24`, `198.51.100.0/24`,
`203.0.113.0/24`) for IP addresses in test input series.  Never use
real infrastructure or production IP addresses in test fixtures.

### Running tests

Run tests locally with:

    CGO_ENABLED=0 go test -v -run TestPrometheusRules ./roles/kube_prometheus_stack/

This requires `promtool` to be available in `$PATH`.

### Checklist

When adding or modifying an alert, ensure the following:

- [ ] The alert has a corresponding entry in `doc/source/admin/monitoring.rst`
- [ ] The entry includes a description, root causes, and remediation steps
- [ ] P1-P3 alerts have a `runbook_url` annotation pointing to the docs
- [ ] The `summary` and `description` annotations follow the format above
- [ ] The alert has negative and positive test cases in `tests.yml`
- [ ] Test expectations include all annotations (summary, description, runbook_url)
- [ ] Tiered or graduated alerts have inhibition rules so higher-severity tiers suppress lower ones
