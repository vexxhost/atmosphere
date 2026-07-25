// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package ciplan

import (
	"fmt"
	"os"
	"slices"

	"github.com/goccy/go-yaml"
	"github.com/vexxhost/atmosphere/internal/deploy"
)

// LoadConfig reads and validates a planner configuration.
func LoadConfig(path string) (Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("reading CI plan configuration: %w", err)
	}
	return ParseConfig(data)
}

// ParseConfig parses and validates planner configuration data.
func ParseConfig(data []byte) (Config, error) {
	var config Config
	if err := yaml.Unmarshal(data, &config); err != nil {
		return Config{}, fmt.Errorf("parsing CI plan configuration: %w", err)
	}
	if err := config.Validate(); err != nil {
		return Config{}, err
	}
	return config, nil
}

// Validate checks references and patterns before any change is planned.
func (c Config) Validate() error {
	if c.Version != 1 {
		return fmt.Errorf("unsupported CI plan configuration version %d", c.Version)
	}
	if c.CanonicalNetworkBackend == "" {
		return fmt.Errorf("canonical_network_backend is required")
	}
	if len(c.FullNetworkBackends) == 0 {
		return fmt.Errorf("full_network_backends must not be empty")
	}
	if !slices.Contains(c.FullNetworkBackends, c.CanonicalNetworkBackend) {
		return fmt.Errorf(
			"canonical network backend %q is not in full_network_backends",
			c.CanonicalNetworkBackend,
		)
	}
	if len(c.FullVerificationProfiles) == 0 {
		return fmt.Errorf("full_verification_profiles must not be empty")
	}

	componentNames := make(map[string]bool, len(deploy.Components))
	for _, component := range deploy.Components {
		componentNames[component.Name] = true
	}

	ruleNames := make(map[string]bool, len(c.Rules))
	for _, rule := range c.Rules {
		if rule.Name == "" {
			return fmt.Errorf("rule name must not be empty")
		}
		if ruleNames[rule.Name] {
			return fmt.Errorf("rule %q is defined more than once", rule.Name)
		}
		ruleNames[rule.Name] = true
		if len(rule.Paths) == 0 {
			return fmt.Errorf("rule %q has no paths", rule.Name)
		}
		switch rule.Action {
		case ActionIgnore, ActionFull:
			if len(rule.Targets) > 0 {
				return fmt.Errorf("rule %q action %q must not define targets", rule.Name, rule.Action)
			}
		case ActionTargets:
			if len(rule.Targets) == 0 {
				return fmt.Errorf("rule %q action targets requires at least one target", rule.Name)
			}
		default:
			return fmt.Errorf("rule %q has unsupported action %q", rule.Name, rule.Action)
		}
		for _, target := range rule.Targets {
			if !componentNames[target] {
				return fmt.Errorf("rule %q references unknown target %q", rule.Name, target)
			}
		}
		for _, pattern := range rule.Paths {
			if _, err := compileGlob(pattern); err != nil {
				return fmt.Errorf("rule %q path %q: %w", rule.Name, pattern, err)
			}
		}
	}

	for name, policy := range c.Components {
		if !componentNames[name] {
			return fmt.Errorf("policy references unknown component %q", name)
		}
		for _, requirement := range policy.TestRequires {
			if !componentNames[requirement] {
				return fmt.Errorf(
					"component %q has unknown test requirement %q",
					name,
					requirement,
				)
			}
		}
		for _, pattern := range policy.Paths {
			if _, err := compileGlob(pattern); err != nil {
				return fmt.Errorf("component %q path %q: %w", name, pattern, err)
			}
		}
	}

	if len(c.Jobs) == 0 {
		return fmt.Errorf("jobs must not be empty")
	}
	verificationProfiles := configuredVerificationProfiles(c)
	for name, policy := range c.Jobs {
		if name == "" {
			return fmt.Errorf("job name must not be empty")
		}
		if policy.Scenario == "" {
			return fmt.Errorf("job %q scenario must not be empty", name)
		}
		if policy.NetworkBackend == "" && len(policy.VerificationProfiles) == 0 {
			return fmt.Errorf(
				"job %q must define network_backend or verification_profiles",
				name,
			)
		}
		if policy.NetworkBackend != "" && len(policy.VerificationProfiles) > 0 {
			return fmt.Errorf(
				"job %q cannot define both network_backend and verification_profiles",
				name,
			)
		}
		if policy.NetworkBackend == "" && len(policy.SkipIfOnlyVerificationProfiles) > 0 {
			return fmt.Errorf(
				"job %q cannot skip profiles without a network_backend",
				name,
			)
		}
		for _, profile := range append(
			slices.Clone(policy.VerificationProfiles),
			policy.SkipIfOnlyVerificationProfiles...,
		) {
			if !verificationProfiles[profile] {
				return fmt.Errorf(
					"job %q references unknown verification profile %q",
					name,
					profile,
				)
			}
		}
	}

	for _, backend := range append(
		slices.Clone(c.FullNetworkBackends),
		configuredBackends(c.Rules, c.Components, c.Jobs)...,
	) {
		if backend == "canonical" {
			continue
		}
		if !slices.Contains(c.FullNetworkBackends, backend) {
			return fmt.Errorf("unknown network backend %q", backend)
		}
	}

	options := deploy.DependencyOptions(c.DependencyOptions)
	for _, backend := range c.FullNetworkBackends {
		optionsForBackend := cloneOptions(options)
		optionsForBackend[deploy.DependencyOptionNetworkBackend] = backend
		if graph, err := deploy.BuildGraphWithOptions(optionsForBackend); err != nil {
			return fmt.Errorf("building deployment graph for backend %q: %w", backend, err)
		} else if _, err := graph.Waves(); err != nil {
			return fmt.Errorf("validating deployment graph for backend %q: %w", backend, err)
		}
		for _, component := range deploy.Components {
			if _, err := deploy.BootstrapComponentNames(
				[]string{component.Name},
				optionsForBackend,
			); err != nil {
				return fmt.Errorf(
					"validating bootstrap closure for component %q on backend %q: %w",
					component.Name,
					backend,
					err,
				)
			}
		}
	}

	return nil
}

func configuredBackends(
	rules []Rule,
	policies map[string]ComponentPolicy,
	jobs map[string]JobPolicy,
) []string {
	var backends []string
	for _, rule := range rules {
		backends = append(backends, rule.NetworkBackends...)
	}
	for _, policy := range policies {
		backends = append(backends, policy.NetworkBackends...)
	}
	for _, job := range jobs {
		if job.NetworkBackend != "" {
			backends = append(backends, job.NetworkBackend)
		}
	}
	return backends
}

func configuredVerificationProfiles(config Config) map[string]bool {
	profiles := make(map[string]bool)
	addAll(profiles, config.FullVerificationProfiles)
	for _, rule := range config.Rules {
		addAll(profiles, rule.VerificationProfiles)
	}
	for _, policy := range config.Components {
		addAll(profiles, policy.VerificationProfiles)
	}
	return profiles
}

func cloneOptions(options map[string]string) map[string]string {
	cloned := make(map[string]string, len(options)+1)
	for key, value := range options {
		cloned[key] = value
	}
	return cloned
}
