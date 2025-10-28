local mixins = import 'mixins.libsonnet';

{
  [mixin]: {
    groups: (mixins[mixin].prometheusAlerts.groups + if std.objectHasAll(mixins[mixin], 'prometheusRules') then mixins[mixin].prometheusRules.groups else []),
  }
  for mixin in std.objectFields(mixins)
}
