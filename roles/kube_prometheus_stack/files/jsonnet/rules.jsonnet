local mixins = import 'mixins.libsonnet';

{
  [mixin]:
    mixins[mixin].prometheusAlerts + (
      if std.objectHasAll(mixins[mixin], 'prometheusRules') then mixins[mixin].prometheusRules else {}
    )
  for mixin in std.objectFields(mixins)
}
