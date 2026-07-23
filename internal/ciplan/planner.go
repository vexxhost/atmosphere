// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package ciplan

import (
	"fmt"
	"path"
	"regexp"
	"slices"
	"sort"
	"strings"

	"github.com/vexxhost/atmosphere/internal/deploy"
)

type compiledRule struct {
	rule     Rule
	patterns []*regexp.Regexp
}

type compiledPolicy struct {
	policy   ComponentPolicy
	patterns []*regexp.Regexp
}

// Planner evaluates changed paths using a validated Config and the deployment
// component registry.
type Planner struct {
	config             Config
	rules              []compiledRule
	policies           map[string]compiledPolicy
	components         map[string]deploy.Component
	rolesToComponents  map[string]string
	chartsToComponents map[string]string
	playbookComponents map[string]string
}

// New creates a planner and precompiles all configured path patterns.
func New(config Config) (*Planner, error) {
	if err := config.Validate(); err != nil {
		return nil, err
	}

	planner := &Planner{
		config:             config,
		policies:           make(map[string]compiledPolicy, len(config.Components)),
		components:         make(map[string]deploy.Component, len(deploy.Components)),
		rolesToComponents:  make(map[string]string, len(deploy.Components)),
		chartsToComponents: make(map[string]string, len(deploy.Components)),
		playbookComponents: make(map[string]string, len(deploy.Components)),
	}

	for _, component := range deploy.Components {
		planner.components[component.Name] = component
		planner.chartsToComponents[component.Name] = component.Name
		if component.RoleName != "" {
			planner.rolesToComponents[component.RoleName] = component.Name
		}
		if component.PreRoleName != "" {
			planner.rolesToComponents[component.PreRoleName] = component.Name
		}
		if component.Playbook != "" {
			planner.playbookComponents[component.Playbook+".yml"] = component.Name
		}
	}

	for _, rule := range config.Rules {
		compiled := compiledRule{rule: rule}
		for _, pattern := range rule.Paths {
			matcher, err := compileGlob(pattern)
			if err != nil {
				return nil, fmt.Errorf("compiling rule %q: %w", rule.Name, err)
			}
			compiled.patterns = append(compiled.patterns, matcher)
		}
		planner.rules = append(planner.rules, compiled)
	}

	for name, policy := range config.Components {
		compiled := compiledPolicy{policy: policy}
		for _, pattern := range policy.Paths {
			matcher, err := compileGlob(pattern)
			if err != nil {
				return nil, fmt.Errorf("compiling component %q: %w", name, err)
			}
			compiled.patterns = append(compiled.patterns, matcher)
		}
		planner.policies[name] = compiled
	}

	return planner, nil
}

// Plan maps changed files to deployment and verification variants.
func (p *Planner) Plan(changes []Change) (Plan, error) {
	if len(changes) == 0 {
		return p.fullPlan(Plan{
			Mode:    ModeFull,
			Reasons: []string{"no changed files were provided, so the planner cannot select a safe subset"},
		}), nil
	}

	normalizedChanges := make([]Change, 0, len(changes))
	targets := map[string]bool{}
	verificationProfiles := map[string]bool{}
	requestedBackends := map[string]bool{}
	var matches []Match
	var reasons []string
	full := false

	for _, change := range changes {
		normalized, err := normalizeChange(change)
		if err != nil {
			return Plan{}, err
		}
		normalizedChanges = append(normalizedChanges, normalized)

		for _, changedPath := range changePaths(normalized) {
			pathMatched := false

			for _, rule := range p.rules {
				if !matchesAny(rule.patterns, changedPath) {
					continue
				}
				pathMatched = true
				matches = append(matches, Match{
					Path:    changedPath,
					Rule:    rule.rule.Name,
					Action:  rule.rule.Action,
					Targets: slices.Clone(rule.rule.Targets),
				})
				switch rule.rule.Action {
				case ActionFull:
					full = true
					reasons = appendUnique(reasons, ruleReason(rule.rule, changedPath))
				case ActionTargets:
					addAll(targets, rule.rule.Targets)
					addAll(verificationProfiles, rule.rule.VerificationProfiles)
					addAll(requestedBackends, rule.rule.NetworkBackends)
				}
			}

			for _, componentName := range p.matchComponents(changedPath) {
				pathMatched = true
				targets[componentName] = true
				matches = append(matches, Match{
					Path:    changedPath,
					Rule:    "component:" + componentName,
					Action:  ActionTargets,
					Targets: []string{componentName},
				})
			}

			if !pathMatched {
				full = true
				reasons = appendUnique(
					reasons,
					fmt.Sprintf("unclassified runtime path %q requires the full fallback", changedPath),
				)
				matches = append(matches, Match{
					Path:   changedPath,
					Rule:   "unclassified",
					Action: ActionFull,
				})
			}
		}
	}

	plan := Plan{
		Changes: normalizedChanges,
		Matches: matches,
		Reasons: reasons,
	}

	if full {
		return p.fullPlan(plan), nil
	}
	if len(targets) == 0 {
		plan.Mode = ModeNoop
		plan.Reasons = appendUnique(plan.Reasons, "all changed paths are ignored by the Molecule policy")
		return plan, nil
	}

	directTargets := sortedKeys(targets)
	deploymentRoots := map[string]bool{}
	queue := slices.Clone(directTargets)
	for len(queue) > 0 {
		name := queue[0]
		queue = queue[1:]
		if deploymentRoots[name] {
			continue
		}
		deploymentRoots[name] = true

		policy := p.policies[name].policy
		for _, requirement := range policy.TestRequires {
			if !deploymentRoots[requirement] {
				queue = append(queue, requirement)
			}
		}
	}

	for _, target := range directTargets {
		policy := p.policies[target].policy
		if len(policy.VerificationProfiles) == 0 {
			verificationProfiles[target] = true
		} else {
			addAll(verificationProfiles, policy.VerificationProfiles)
		}
		addAll(requestedBackends, policy.NetworkBackends)
	}
	if len(requestedBackends) == 0 {
		requestedBackends["canonical"] = true
	}

	backends, err := p.resolveBackends(sortedKeys(requestedBackends))
	if err != nil {
		return Plan{}, err
	}
	roots := sortedKeys(deploymentRoots)

	plan.Mode = ModeSelective
	plan.Targets = directTargets
	plan.DeploymentRoots = roots
	plan.VerificationProfiles = sortedKeys(verificationProfiles)

	for _, backend := range backends {
		options := cloneOptions(p.config.DependencyOptions)
		options[deploy.DependencyOptionNetworkBackend] = backend
		components, err := deploy.BootstrapComponentNames(
			roots,
			deploy.DependencyOptions(options),
		)
		if err != nil {
			return Plan{}, fmt.Errorf("planning backend %q: %w", backend, err)
		}
		plan.Variants = append(plan.Variants, Variant{
			NetworkBackend:    backend,
			DependencyOptions: options,
			Components:        components,
		})
	}

	return plan, nil
}

func (p *Planner) fullPlan(plan Plan) Plan {
	plan.Mode = ModeFull
	plan.VerificationProfiles = slices.Clone(p.config.FullVerificationProfiles)

	components := make([]string, 0, len(p.components))
	for name := range p.components {
		components = append(components, name)
	}
	sort.Strings(components)

	for _, backend := range p.config.FullNetworkBackends {
		options := cloneOptions(p.config.DependencyOptions)
		options[deploy.DependencyOptionNetworkBackend] = backend
		plan.Variants = append(plan.Variants, Variant{
			NetworkBackend:    backend,
			DependencyOptions: options,
			Components:        slices.Clone(components),
		})
	}
	return plan
}

func (p *Planner) matchComponents(changedPath string) []string {
	matched := map[string]bool{}
	segments := strings.Split(changedPath, "/")

	if len(segments) >= 3 && segments[0] == "roles" {
		if component, ok := p.rolesToComponents[segments[1]]; ok {
			matched[component] = true
		}
	}
	if len(segments) >= 3 && segments[0] == "charts" && segments[1] != "patches" {
		if component, ok := p.chartsToComponents[segments[1]]; ok {
			matched[component] = true
		}
	}
	if len(segments) >= 4 && segments[0] == "charts" && segments[1] == "patches" {
		if component, ok := p.chartsToComponents[segments[2]]; ok {
			matched[component] = true
		}
	}
	if len(segments) == 2 && segments[0] == "playbooks" {
		if component, ok := p.playbookComponents[segments[1]]; ok {
			matched[component] = true
		}
	}

	for name, policy := range p.policies {
		if matchesAny(policy.patterns, changedPath) {
			matched[name] = true
		}
	}
	return sortedKeys(matched)
}

func (p *Planner) resolveBackends(requested []string) ([]string, error) {
	resolved := map[string]bool{}
	for _, backend := range requested {
		if backend == "canonical" {
			backend = p.config.CanonicalNetworkBackend
		}
		if !slices.Contains(p.config.FullNetworkBackends, backend) {
			return nil, fmt.Errorf("network backend %q is not configured", backend)
		}
		resolved[backend] = true
	}
	return sortedKeys(resolved), nil
}

func normalizeChange(change Change) (Change, error) {
	var err error
	change.Path, err = normalizeRepoPath(change.Path)
	if err != nil {
		return Change{}, fmt.Errorf("normalizing changed path: %w", err)
	}
	if change.PreviousPath != "" {
		change.PreviousPath, err = normalizeRepoPath(change.PreviousPath)
		if err != nil {
			return Change{}, fmt.Errorf("normalizing previous path: %w", err)
		}
	}
	if change.Status == "" {
		change.Status = "M"
	}
	return change, nil
}

func normalizeRepoPath(value string) (string, error) {
	value = strings.TrimPrefix(strings.ReplaceAll(value, "\\", "/"), "./")
	cleaned := path.Clean(value)
	if value == "" || cleaned == "." {
		return "", fmt.Errorf("path must not be empty")
	}
	if strings.HasPrefix(cleaned, "../") || strings.HasPrefix(cleaned, "/") {
		return "", fmt.Errorf("path %q is outside the repository", value)
	}
	return cleaned, nil
}

func changePaths(change Change) []string {
	paths := []string{change.Path}
	if change.PreviousPath != "" && change.PreviousPath != change.Path {
		paths = append(paths, change.PreviousPath)
	}
	return paths
}

func matchesAny(patterns []*regexp.Regexp, value string) bool {
	for _, pattern := range patterns {
		if pattern.MatchString(value) {
			return true
		}
	}
	return false
}

func addAll(set map[string]bool, values []string) {
	for _, value := range values {
		set[value] = true
	}
}

func appendUnique(values []string, value string) []string {
	if slices.Contains(values, value) {
		return values
	}
	return append(values, value)
}

func sortedKeys(values map[string]bool) []string {
	keys := make([]string, 0, len(values))
	for key := range values {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

func ruleReason(rule Rule, changedPath string) string {
	if rule.Reason != "" {
		return fmt.Sprintf("%s: %s", changedPath, rule.Reason)
	}
	return fmt.Sprintf("%s matched full-fallback rule %q", changedPath, rule.Name)
}
