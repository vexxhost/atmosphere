{
  mapRuleGroups(f): {
    groups: [
      group {
        rules: [
          f(rule, group)
          for rule in super.rules
        ],
      }
      for group in super.groups
    ],
  },
}
