# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Plan the smallest safe set of Molecule jobs for a repository change."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

import yaml


class PolicyError(ValueError):
    """Raised when the selective CI policy is invalid."""


@dataclass(frozen=True)
class Change:
    """One path reported by ``git diff --name-status``."""

    status: str
    path: str
    previous_path: str | None = None


def _strings(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PolicyError(f"{field} must be a list of strings")
    duplicates = sorted({item for item in value if value.count(item) > 1})
    if duplicates:
        raise PolicyError(f"{field} contains duplicate values: {', '.join(duplicates)}")
    return list(value)


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise PolicyError(f"{field} must be a mapping with string keys")
    return value


def _normalize_path(value: str) -> str:
    normalized = value.replace("\\", "/").removeprefix("./")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise PolicyError(f"repository path {value!r} is invalid")
    return str(path)


def _compile_glob(pattern: str) -> re.Pattern[str]:
    """Compile a repository glob where ``*`` never crosses a slash."""

    output = ["^"]
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == "*":
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
                output.append(".*")
                index += 2
                continue
            output.append("[^/]*")
        elif character == "?":
            output.append("[^/]")
        else:
            output.append(re.escape(character).replace(r"\-", "-"))
        index += 1
    output.append("$")
    return re.compile("".join(output))


def _unique(values: Iterable[str]) -> list[str]:
    """Return values in their original order without duplicates."""

    return list(dict.fromkeys(values))


def _grouped_regexes(
    prefix: str,
    values: Iterable[str],
    suffix: str,
    max_length: int = 100,
) -> list[str]:
    """Group escaped alternatives into readable regular expressions."""

    groups: list[list[str]] = []
    for value in sorted(values):
        escaped = re.escape(value).replace(r"\-", "-")
        if (
            groups
            and len(prefix + "|".join(groups[-1] + [escaped]) + suffix) <= max_length
        ):
            groups[-1].append(escaped)
        else:
            groups.append([escaped])
    return [prefix + "|".join(group) + suffix for group in groups]


def parse_changes(lines: Iterable[str]) -> list[Change]:
    """Parse paths or ``git diff --name-status`` records."""

    changes: list[Change] = []
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) == 1:
            changes.append(Change(status="M", path=_normalize_path(fields[0])))
        elif len(fields) == 2 and all(fields):
            changes.append(Change(status=fields[0], path=_normalize_path(fields[1])))
        elif len(fields) == 3 and fields[0].startswith(("R", "C")) and all(fields):
            changes.append(
                Change(
                    status=fields[0],
                    previous_path=_normalize_path(fields[1]),
                    path=_normalize_path(fields[2]),
                )
            )
        else:
            raise PolicyError(
                f"invalid changed-file record on line {line_number}: {line!r}"
            )
    return changes


def git_changes(base: str, head: str) -> list[Change]:
    """Return changes belonging to ``base...head``."""

    if not base.strip() or not head.strip():
        raise PolicyError("both base and head revisions are required")
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-status",
            "--find-renames",
            f"{base}...{head}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_changes(result.stdout.splitlines())


class Planner:
    """Map changed files to static Zuul jobs and sequential Ansible tags."""

    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.jobs = _mapping(policy.get("jobs"), "jobs")
        self.components = _mapping(policy.get("components"), "components")
        self.verification_checks = _mapping(
            policy.get("verification_checks", {}),
            "verification_checks",
        )
        rules = policy.get("rules")
        if not isinstance(rules, list):
            raise PolicyError("rules must be a list")
        self.rules: list[dict[str, Any]] = []
        self._compiled_rule_paths: dict[str, list[re.Pattern[str]]] = {}
        self._compiled_component_paths: dict[str, list[re.Pattern[str]]] = {}
        self._validate(rules)

    @classmethod
    def load(cls, path: str | Path) -> "Planner":
        with Path(path).open(encoding="utf-8") as stream:
            policy = yaml.safe_load(stream)
        if not isinstance(policy, dict):
            raise PolicyError("policy document must be a mapping")
        return cls(policy)

    def _validate(self, rules: list[Any]) -> None:
        if self.policy.get("version") != 1:
            raise PolicyError("policy version must be 1")
        if not self.jobs:
            raise PolicyError("at least one job must be configured")
        if not self.components:
            raise PolicyError("at least one component must be configured")

        for job_name, job_value in self.jobs.items():
            job = _mapping(job_value, f"jobs.{job_name}")
            if not isinstance(job.get("scenario"), str) or not job["scenario"]:
                raise PolicyError(f"jobs.{job_name}.scenario must be a string")
            backend = job.get("network_backend")
            if backend is not None and not isinstance(backend, str):
                raise PolicyError(f"jobs.{job_name}.network_backend must be a string")

        full_jobs = _strings(self.policy.get("full_jobs"), "full_jobs")
        if not full_jobs:
            raise PolicyError("full_jobs must not be empty")
        self._check_jobs(full_jobs, "full_jobs")

        for profile, checks in self.verification_checks.items():
            if not isinstance(checks, list):
                raise PolicyError(
                    f"verification_checks.{profile} must be a list of mappings"
                )
            for index, check_value in enumerate(checks):
                field = f"verification_checks.{profile}[{index}]"
                check = _mapping(check_value, field)
                unexpected = sorted(set(check) - {"service", "type"})
                if unexpected:
                    raise PolicyError(
                        f"{field} contains unsupported keys: "
                        f"{', '.join(unexpected)}"
                    )
                for key in ("service", "type"):
                    if not isinstance(check.get(key), str) or not check[key]:
                        raise PolicyError(f"{field}.{key} must be a string")

        owners: dict[tuple[str, str], str] = {}
        for component_name, component_value in self.components.items():
            component = _mapping(component_value, f"components.{component_name}")
            requires = _strings(
                component.get("requires"), f"components.{component_name}.requires"
            )
            test_requires = _strings(
                component.get("test_requires"),
                f"components.{component_name}.test_requires",
            )
            for dependency in requires + test_requires:
                if dependency not in self.components:
                    raise PolicyError(
                        f"component {component_name!r} requires unknown "
                        f"component {dependency!r}"
                    )
            backend_requires = _mapping(
                component.get("backend_requires", {}),
                f"components.{component_name}.backend_requires",
            )
            for backend, dependencies in backend_requires.items():
                for dependency in _strings(
                    dependencies,
                    f"components.{component_name}.backend_requires.{backend}",
                ):
                    if dependency not in self.components:
                        raise PolicyError(
                            f"component {component_name!r} requires unknown "
                            f"component {dependency!r} for backend {backend!r}"
                        )
            component_jobs = _strings(
                component.get("jobs"), f"components.{component_name}.jobs"
            )
            if not component_jobs:
                raise PolicyError(f"component {component_name!r} has no jobs")
            self._check_jobs(component_jobs, f"components.{component_name}.jobs")
            _strings(
                component.get("verification_profiles"),
                f"components.{component_name}.verification_profiles",
            )
            tempest_tests = _strings(
                component.get("tempest_tests"),
                f"components.{component_name}.tempest_tests",
            )
            for index, pattern in enumerate(tempest_tests):
                try:
                    re.compile(pattern)
                except re.error as error:
                    raise PolicyError(
                        f"components.{component_name}.tempest_tests[{index}] "
                        f"is not a valid regular expression: {error}"
                    ) from error

            for owner_type, values in (
                (
                    "role",
                    _strings(
                        component.get("roles", [component_name.replace("-", "_")]),
                        f"components.{component_name}.roles",
                    ),
                ),
                (
                    "chart",
                    _strings(
                        component.get("charts", [component_name]),
                        f"components.{component_name}.charts",
                    ),
                ),
            ):
                for value in values:
                    key = (owner_type, value)
                    if key in owners:
                        raise PolicyError(
                            f"{owner_type} {value!r} is owned by both "
                            f"{owners[key]!r} and {component_name!r}"
                        )
                    owners[key] = component_name

            component_paths = _strings(
                component.get("paths"), f"components.{component_name}.paths"
            )
            self._compiled_component_paths[component_name] = [
                _compile_glob(pattern) for pattern in component_paths
            ]

        seen_rules: set[str] = set()
        for index, rule_value in enumerate(rules):
            rule = _mapping(rule_value, f"rules[{index}]")
            name = rule.get("name")
            if not isinstance(name, str) or not name:
                raise PolicyError(f"rules[{index}].name must be a string")
            if name in seen_rules:
                raise PolicyError(f"rule name {name!r} is duplicated")
            seen_rules.add(name)
            action = rule.get("action")
            if action not in {"full", "ignore", "targets"}:
                raise PolicyError(f"rule {name!r} has unsupported action {action!r}")
            paths = _strings(rule.get("paths"), f"rules.{name}.paths")
            if not paths:
                raise PolicyError(f"rule {name!r} has no paths")
            targets = _strings(rule.get("targets"), f"rules.{name}.targets")
            for target in targets:
                if target not in self.components:
                    raise PolicyError(
                        f"rule {name!r} targets unknown component {target!r}"
                    )
            rule_jobs = _strings(rule.get("jobs"), f"rules.{name}.jobs")
            self._check_jobs(rule_jobs, f"rules.{name}.jobs")
            if action == "targets" and not targets:
                raise PolicyError(f"target rule {name!r} has no targets")
            self.rules.append(rule)
            self._compiled_rule_paths[name] = [
                _compile_glob(pattern) for pattern in paths
            ]

        self._validate_cycles()

    def _check_jobs(self, jobs: Iterable[str], field: str) -> None:
        for job in jobs:
            if job not in self.jobs:
                raise PolicyError(f"{field} references unknown job {job!r}")

    def _validate_cycles(self) -> None:
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(name: str) -> None:
            if name in permanent:
                return
            if name in temporary:
                raise PolicyError(
                    f"component dependency graph contains a cycle at {name!r}"
                )
            temporary.add(name)
            component = self.components[name]
            dependencies = _strings(
                component.get("requires"), f"components.{name}.requires"
            )
            backend_requires = _mapping(
                component.get("backend_requires", {}),
                f"components.{name}.backend_requires",
            )
            for values in backend_requires.values():
                dependencies.extend(_strings(values, f"components.{name}"))
            for dependency in dependencies:
                visit(dependency)
            temporary.remove(name)
            permanent.add(name)

        for component_name in self.components:
            visit(component_name)

    def plan(self, changes: Sequence[Change]) -> dict[str, Any]:
        normalized_changes = [
            Change(
                status=change.status or "M",
                path=_normalize_path(change.path),
                previous_path=(
                    _normalize_path(change.previous_path)
                    if change.previous_path
                    else None
                ),
            )
            for change in changes
        ]
        if not normalized_changes:
            return self._full_plan(
                normalized_changes,
                [],
                [
                    "no changed files were provided, so the planner cannot "
                    "select a safe subset"
                ],
            )

        matches: list[dict[str, Any]] = []
        reasons: list[str] = []
        targets: set[str] = set()
        job_targets: dict[str, set[str]] = {job_name: set() for job_name in self.jobs}
        full = False

        for change in normalized_changes:
            paths = [change.path]
            if change.previous_path and change.previous_path != change.path:
                paths.append(change.previous_path)
            for changed_path in paths:
                matched = False
                for rule in self.rules:
                    if not self._matches(
                        self._compiled_rule_paths[rule["name"]], changed_path
                    ):
                        continue
                    matched = True
                    action = rule["action"]
                    rule_targets = _strings(
                        rule.get("targets"), f"rules.{rule['name']}.targets"
                    )
                    matches.append(
                        {
                            "path": changed_path,
                            "rule": rule["name"],
                            "action": action,
                            "targets": rule_targets,
                        }
                    )
                    if action == "full":
                        full = True
                        reasons.append(
                            rule.get("reason")
                            or f"{changed_path} matched full rule {rule['name']}"
                        )
                    elif action == "targets":
                        targets.update(rule_targets)
                        rule_jobs = _strings(
                            rule.get("jobs"), f"rules.{rule['name']}.jobs"
                        )
                        for job_name in rule_jobs:
                            job_targets[job_name].update(rule_targets)

                for component_name in self._match_components(changed_path):
                    matched = True
                    targets.add(component_name)
                    component = self.components[component_name]
                    component_jobs = _strings(
                        component.get("jobs"),
                        f"components.{component_name}.jobs",
                    )
                    for job_name in component_jobs:
                        job_targets[job_name].add(component_name)
                    matches.append(
                        {
                            "path": changed_path,
                            "rule": f"component:{component_name}",
                            "action": "targets",
                            "targets": [component_name],
                        }
                    )

                if not matched:
                    full = True
                    reasons.append(
                        f"unclassified runtime path {changed_path!r} requires "
                        "the full fallback"
                    )
                    matches.append(
                        {
                            "path": changed_path,
                            "rule": "unclassified",
                            "action": "full",
                            "targets": [],
                        }
                    )

        if full:
            return self._full_plan(normalized_changes, matches, reasons)
        if not targets:
            return self._noop_plan(normalized_changes, matches)

        decisions: dict[str, dict[str, Any]] = {}
        variants: list[dict[str, Any]] = []
        all_profiles: set[str] = set()
        for target in targets:
            all_profiles.update(
                _strings(
                    self.components[target].get("verification_profiles"),
                    f"components.{target}.verification_profiles",
                )
            )
        all_tempest_tests = self._tempest_test_patterns(targets)
        all_verification_checks = self._verification_checks(targets)

        for job_name, job_value in self.jobs.items():
            job = _mapping(job_value, f"jobs.{job_name}")
            roots = sorted(job_targets[job_name])
            if not roots:
                decisions[job_name] = self._skip_decision(
                    job_name, job, "no changed component requires this job"
                )
                continue

            scenario = job["scenario"]
            backend = job.get("network_backend")
            if scenario == "aio":
                deployment_roots = self._test_roots(roots)
                components = self._closure(deployment_roots, backend)
                tags = [self.components[name].get("tag", name) for name in components]
                profiles = sorted(
                    {
                        profile
                        for root in roots
                        for profile in _strings(
                            self.components[root].get("verification_profiles"),
                            f"components.{root}.verification_profiles",
                        )
                    }
                )
                tempest_tests = self._tempest_test_patterns(roots)
                verification_checks = self._verification_checks(roots)
                decision = {
                    "run": True,
                    "reason": "selected by changed components",
                    "scenario": scenario,
                    "network_backend": backend,
                    "targets": roots,
                    "components": components,
                    "ansible_tags": tags,
                    "verification_profiles": profiles,
                    "verification_checks": verification_checks,
                    "tempest_tests": tempest_tests,
                    "run_tempest": self._tempest_required(roots),
                }
                variants.append(
                    {
                        "job": job_name,
                        "network_backend": backend,
                        "targets": roots,
                        "deployment_roots": deployment_roots,
                        "components": components,
                        "ansible_tags": tags,
                        "verification_profiles": profiles,
                        "verification_checks": verification_checks,
                        "tempest_tests": tempest_tests,
                        "run_tempest": self._tempest_required(roots),
                    }
                )
            else:
                decision = {
                    "run": True,
                    "reason": "selected by changed components",
                    "scenario": scenario,
                    "network_backend": backend,
                    "targets": roots,
                    "components": [],
                    "ansible_tags": [],
                    "verification_profiles": sorted(all_profiles),
                    "verification_checks": all_verification_checks,
                    "tempest_tests": all_tempest_tests,
                    "run_tempest": False,
                }
            decisions[job_name] = decision

        return {
            "version": 1,
            "mode": "selective",
            "changes": [asdict(change) for change in normalized_changes],
            "matches": matches,
            "targets": sorted(targets),
            "verification_profiles": sorted(all_profiles),
            "verification_checks": all_verification_checks,
            "tempest_tests": all_tempest_tests,
            "variants": variants,
            "job_decisions": decisions,
            "reasons": reasons,
        }

    def scheduler_irrelevant_files(self) -> dict[str, list[str]]:
        """Build conservative Zuul filters from the impact policy.

        An unclassified path is intentionally absent from every list so it
        still schedules the complete fallback. A path is irrelevant to a job
        only when the policy explicitly ignores it or assigns it exclusively
        to other jobs.
        """

        irrelevant: dict[str, list[str]] = {job_name: [] for job_name in self.jobs}
        unrelated_roles: dict[str, set[str]] = {
            job_name: set() for job_name in self.jobs
        }
        unrelated_charts: dict[str, set[str]] = {
            job_name: set() for job_name in self.jobs
        }

        def add(job_names: Iterable[str], patterns: Iterable[str]) -> None:
            compiled = [_compile_glob(pattern).pattern for pattern in patterns]
            for job_name in job_names:
                irrelevant[job_name].extend(compiled)

        all_jobs = set(self.jobs)
        for rule in self.rules:
            action = rule["action"]
            if action == "ignore":
                irrelevant_jobs = all_jobs
            elif action == "targets":
                relevant_jobs = set(
                    _strings(rule.get("jobs"), f"rules.{rule['name']}.jobs")
                )
                irrelevant_jobs = all_jobs - relevant_jobs
            else:
                continue
            add(
                sorted(irrelevant_jobs),
                _strings(rule.get("paths"), f"rules.{rule['name']}.paths"),
            )

        for component_name, component_value in self.components.items():
            component = _mapping(component_value, f"components.{component_name}")
            relevant_jobs = set(
                _strings(
                    component.get("jobs"),
                    f"components.{component_name}.jobs",
                )
            )
            irrelevant_jobs = all_jobs - relevant_jobs
            add(
                sorted(irrelevant_jobs),
                _strings(
                    component.get("paths"),
                    f"components.{component_name}.paths",
                ),
            )
            roles = _strings(
                component.get("roles", [component_name.replace("-", "_")]),
                f"components.{component_name}.roles",
            )
            charts = _strings(
                component.get("charts", [component_name]),
                f"components.{component_name}.charts",
            )
            for job_name in irrelevant_jobs:
                unrelated_roles[job_name].update(roles)
                unrelated_charts[job_name].update(charts)

        for job_name in self.jobs:
            if unrelated_roles[job_name]:
                irrelevant[job_name].extend(
                    _grouped_regexes(
                        "^roles/(",
                        unrelated_roles[job_name],
                        ")/.*$",
                    )
                )
            if unrelated_charts[job_name]:
                irrelevant[job_name].extend(
                    _grouped_regexes(
                        "^charts/(patches/)?(",
                        unrelated_charts[job_name],
                        ")/.*$",
                    )
                )
            irrelevant[job_name] = _unique(irrelevant[job_name])
        return irrelevant

    def _match_components(self, path: str) -> list[str]:
        matched: set[str] = set()
        parts = path.split("/")
        role_name: str | None = None
        chart_name: str | None = None
        if len(parts) >= 3 and parts[0] == "roles":
            role_name = parts[1]
        elif len(parts) >= 3 and parts[0] == "charts":
            if parts[1] == "patches" and len(parts) >= 4:
                chart_name = parts[2]
            else:
                chart_name = parts[1]

        for component_name, component_value in self.components.items():
            component = _mapping(component_value, f"components.{component_name}")
            if role_name and role_name in _strings(
                component.get("roles", [component_name.replace("-", "_")]),
                f"components.{component_name}.roles",
            ):
                matched.add(component_name)
            if chart_name and chart_name in _strings(
                component.get("charts", [component_name]),
                f"components.{component_name}.charts",
            ):
                matched.add(component_name)
            if self._matches(self._compiled_component_paths[component_name], path):
                matched.add(component_name)
        return sorted(matched)

    @staticmethod
    def _matches(patterns: Iterable[re.Pattern[str]], path: str) -> bool:
        return any(pattern.match(path) for pattern in patterns)

    def _closure(self, roots: Iterable[str], backend: str | None) -> list[str]:
        closure: set[str] = set()

        def visit(name: str) -> None:
            if name in closure:
                return
            closure.add(name)
            component = self.components[name]
            dependencies = _strings(
                component.get("requires"), f"components.{name}.requires"
            )
            if backend:
                backend_requires = _mapping(
                    component.get("backend_requires", {}),
                    f"components.{name}.backend_requires",
                )
                dependencies.extend(
                    _strings(
                        backend_requires.get(backend),
                        f"components.{name}.backend_requires.{backend}",
                    )
                )
            for dependency in dependencies:
                visit(dependency)

        for root in roots:
            visit(root)
        return sorted(closure)

    def _test_roots(self, targets: Iterable[str]) -> list[str]:
        roots: set[str] = set()

        def visit(name: str) -> None:
            if name in roots:
                return
            roots.add(name)
            for requirement in _strings(
                self.components[name].get("test_requires"),
                f"components.{name}.test_requires",
            ):
                visit(requirement)

        for target in targets:
            visit(target)
        return sorted(roots)

    def _tempest_test_patterns(self, targets: Iterable[str]) -> list[str]:
        patterns: set[str] = set()
        for target in targets:
            target_patterns = _strings(
                self.components[target].get("tempest_tests"),
                f"components.{target}.tempest_tests",
            )
            if not target_patterns and not self._verification_checks([target]):
                return []
            patterns.update(target_patterns)
        return sorted(patterns)

    def _verification_checks(
        self,
        targets: Iterable[str],
    ) -> list[dict[str, str]]:
        checks: dict[tuple[str, str], dict[str, str]] = {}
        for target in targets:
            profiles = _strings(
                self.components[target].get("verification_profiles"),
                f"components.{target}.verification_profiles",
            )
            for profile in profiles:
                for check_value in self.verification_checks.get(profile, []):
                    check = _mapping(
                        check_value,
                        f"verification_checks.{profile}",
                    )
                    key = (check["service"], check["type"])
                    checks[key] = {
                        "service": check["service"],
                        "type": check["type"],
                    }
        return [checks[key] for key in sorted(checks)]

    def _tempest_required(self, targets: Iterable[str]) -> bool:
        for target in targets:
            if _strings(
                self.components[target].get("tempest_tests"),
                f"components.{target}.tempest_tests",
            ):
                return True
            if not self._verification_checks([target]):
                return True
        return False

    def _full_plan(
        self,
        changes: Sequence[Change],
        matches: list[dict[str, Any]],
        reasons: list[str],
    ) -> dict[str, Any]:
        full_jobs = set(_strings(self.policy["full_jobs"], "full_jobs"))
        decisions: dict[str, dict[str, Any]] = {}
        for job_name, job_value in self.jobs.items():
            job = _mapping(job_value, f"jobs.{job_name}")
            if job_name in full_jobs:
                decisions[job_name] = {
                    "run": True,
                    "reason": "full fallback",
                    "scenario": job["scenario"],
                    "network_backend": job.get("network_backend"),
                    "targets": [],
                    "components": [],
                    "ansible_tags": [],
                    "verification_profiles": ["full"],
                    "verification_checks": [],
                    "tempest_tests": [],
                    "run_tempest": job["scenario"] == "aio",
                }
            else:
                decisions[job_name] = self._skip_decision(
                    job_name, job, "job is not part of the full fallback"
                )
        return {
            "version": 1,
            "mode": "full",
            "changes": [asdict(change) for change in changes],
            "matches": matches,
            "targets": [],
            "verification_profiles": ["full"],
            "verification_checks": [],
            "tempest_tests": [],
            "variants": [],
            "job_decisions": decisions,
            "reasons": list(dict.fromkeys(reasons)),
        }

    def _noop_plan(
        self,
        changes: Sequence[Change],
        matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        decisions = {
            job_name: self._skip_decision(
                job_name,
                _mapping(job, f"jobs.{job_name}"),
                "all changed paths are ignored",
            )
            for job_name, job in self.jobs.items()
        }
        return {
            "version": 1,
            "mode": "noop",
            "changes": [asdict(change) for change in changes],
            "matches": matches,
            "targets": [],
            "verification_profiles": [],
            "verification_checks": [],
            "tempest_tests": [],
            "variants": [],
            "job_decisions": decisions,
            "reasons": ["all changed paths are ignored by the Molecule policy"],
        }

    @staticmethod
    def _skip_decision(
        job_name: str, job: dict[str, Any], reason: str
    ) -> dict[str, Any]:
        del job_name
        return {
            "run": False,
            "reason": reason,
            "scenario": job["scenario"],
            "network_backend": job.get("network_backend"),
            "targets": [],
            "components": [],
            "ansible_tags": [],
            "verification_profiles": [],
            "verification_checks": [],
            "tempest_tests": [],
            "run_tempest": False,
        }


def render_plan(plan: dict[str, Any]) -> str:
    """Render a plan for readable Zuul console output."""

    lines = [f"Selective Molecule plan: {plan['mode']}"]
    lines.append("Changed files:")
    for change in plan.get("changes", []):
        if change.get("previous_path"):
            lines.append(
                f"  {change['status']} {change['previous_path']} -> "
                f"{change['path']}"
            )
        else:
            lines.append(f"  {change['status']} {change['path']}")
    if not plan.get("changes"):
        lines.append("  (none)")
    if plan.get("targets"):
        lines.append(f"Targets: {', '.join(plan['targets'])}")
    lines.append("Job decisions:")
    for job_name, decision in plan["job_decisions"].items():
        state = "RUN" if decision["run"] else "SKIP"
        lines.append(f"  {state:4} {job_name}: {decision['reason']}")
        if decision["run"] and decision.get("components"):
            lines.append("       components: " + ", ".join(decision["components"]))
        if decision["run"] and decision.get("tempest_tests"):
            lines.append(
                "       Tempest include: " + ", ".join(decision["tempest_tests"])
            )
        if decision["run"] and decision.get("verification_checks"):
            checks = (
                f"{check['service']}/{check['type']}"
                for check in decision["verification_checks"]
            )
            lines.append("       API checks: " + ", ".join(checks))
    for reason in plan.get("reasons", []):
        lines.append(f"Reason: {reason}")
    return "\n".join(lines)


def _load_plan(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as stream:
        plan = json.load(stream)
    if not isinstance(plan, dict) or "job_decisions" not in plan:
        raise PolicyError(f"{path} is not a selective CI plan")
    return plan


def _write_output(value: str, output: str) -> None:
    if output == "-":
        print(value)
    else:
        Path(output).write_text(value + "\n", encoding="utf-8")


def _collect_changes(args: argparse.Namespace) -> list[Change]:
    sources = sum(
        (
            bool(args.changed_file),
            bool(args.files_from),
            bool(args.base or args.head),
        )
    )
    if sources != 1:
        raise PolicyError(
            "provide exactly one change source: --changed-file, --files-from, "
            "or --base with --head"
        )
    if args.changed_file:
        return [
            Change(status="M", path=_normalize_path(path)) for path in args.changed_file
        ]
    if args.files_from:
        if args.files_from == "-":
            return parse_changes(sys.stdin)
        with Path(args.files_from).open(encoding="utf-8") as stream:
            return parse_changes(stream)
    if not args.base or not args.head:
        raise PolicyError("--base and --head must be provided together")
    return git_changes(args.base, args.head)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan selective Atmosphere Molecule jobs"
    )
    parser.add_argument(
        "--config",
        default="ci/molecule-plan.yaml",
        help="selective CI policy",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="validate the policy")

    plan = subparsers.add_parser("plan", help="create a plan")
    plan.add_argument("--changed-file", action="append", default=[])
    plan.add_argument("--files-from")
    plan.add_argument("--base")
    plan.add_argument("--head")
    plan.add_argument("--format", choices=("json", "text"), default="text")
    plan.add_argument("--output", default="-")

    render = subparsers.add_parser("render", help="render a JSON plan")
    render.add_argument("plan")
    subparsers.add_parser(
        "scheduler-files",
        help="render Zuul irrelevant-files derived from the policy",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            print(render_plan(_load_plan(args.plan)))
            return 0

        planner = Planner.load(args.config)
        if args.command == "validate":
            print(f"Selective CI policy {args.config} is valid")
            return 0
        if args.command == "scheduler-files":
            print(
                yaml.safe_dump(
                    planner.scheduler_irrelevant_files(),
                    sort_keys=False,
                ).rstrip()
            )
            return 0

        plan = planner.plan(_collect_changes(args))
        if args.format == "json":
            value = json.dumps(plan, indent=2)
        else:
            value = render_plan(plan)
        _write_output(value, args.output)
        return 0
    except (OSError, PolicyError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
