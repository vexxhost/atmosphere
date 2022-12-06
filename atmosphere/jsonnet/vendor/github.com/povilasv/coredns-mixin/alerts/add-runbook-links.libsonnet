local utils = import '../lib/utils.libsonnet';

local lower(x) =
  local cp(c) = std.codepoint(c);
  local lowerLetter(c) =
    if cp(c) >= 65 && cp(c) < 91
    then std.char(cp(c) + 32)
    else c;
  std.join('', std.map(lowerLetter, std.stringChars(x)));

{
  _config+:: {
    corednsRunbookURLPattern: 'https://github.com/povilasv/coredns-mixin/tree/master/runbook.md#alert-name-%s',
  },

  prometheusAlerts+::
    local addRunbookURL(rule, group) = rule {
      [if 'alert' in rule && std.member(['coredns', 'coredns_forward'], group.name) then 'annotations']+: {
        runbook_url: $._config.corednsRunbookURLPattern % lower(rule.alert),
      },
    };
    utils.mapRuleGroups(addRunbookURL),
}
