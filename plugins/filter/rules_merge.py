# SPDX-License-Identifier: Apache-2.0
# Copyright (c) VEXXHOST, Inc.

from ansible.errors import AnsibleFilterError


def rules_merge(rules, **kwargs):
    list_merge = kwargs.pop("list_merge", "replace")
    if list_merge not in ("replace", "append"):
        raise AnsibleFilterError(
            "'replace' and 'append' are the only valid value for 'list_merge'"
        )
    if kwargs:
        raise AnsibleFilterError("'list_merge' is the only valid keyword argument")

    for rule_name in rules:
        merged_groups = dict()
        rule = rules[rule_name]
        if "groups" not in rule:
            continue
        for group in rule["groups"]:
            if list_merge == "append" and group["name"] in merged_groups:
                merged_groups[group["name"]]["rules"] += group["rules"]
                # combine merged_groups[group["name"]]["rules"] and group["rules"]
                counts = []
                pops = []
                for idx, ru in enumerate(merged_groups[group["name"]]["rules"]):
                    ru_tup = tuple(sorted(ru.items()))
                    if ru_tup in counts:
                        pops.append(idx)
                    else:
                        counts.append(ru_tup)
                for i in reversed(pops):
                    del merged_groups[group["name"]]["rules"][i]
            else:
                merged_groups[group["name"]] = group

        rule["groups"] = list(merged_groups.values())
        rules[rule_name] = rule
    return rules


class FilterModule(object):
    def filters(self):
        return {
            "rules_merge": rules_merge,
        }
