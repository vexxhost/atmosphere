// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

// Package ciplan maps changed repository files to the smallest safe Molecule
// deployment and verification plan.
package ciplan

// Change describes a changed repository path. PreviousPath is populated for
// renames and copies so both sides of the change are evaluated.
type Change struct {
	Status       string `json:"status"`
	Path         string `json:"path"`
	PreviousPath string `json:"previous_path,omitempty"`
}

// Config is the declarative CI impact and verification policy.
type Config struct {
	Version                  int                        `yaml:"version"`
	CanonicalNetworkBackend  string                     `yaml:"canonical_network_backend"`
	FullNetworkBackends      []string                   `yaml:"full_network_backends"`
	DependencyOptions        map[string]string          `yaml:"dependency_options"`
	Rules                    []Rule                     `yaml:"rules"`
	Components               map[string]ComponentPolicy `yaml:"components"`
	Jobs                     map[string]JobPolicy       `yaml:"jobs"`
	FullVerificationProfiles []string                   `yaml:"full_verification_profiles"`
}

// Rule handles shared, ignored, or otherwise non-component-specific paths.
type Rule struct {
	Name                 string   `yaml:"name"`
	Paths                []string `yaml:"paths"`
	Action               string   `yaml:"action"`
	Targets              []string `yaml:"targets"`
	VerificationProfiles []string `yaml:"verification_profiles"`
	NetworkBackends      []string `yaml:"network_backends"`
	Reason               string   `yaml:"reason"`
}

// ComponentPolicy adds functional-test requirements and verification metadata
// to a deployable component from the deployment registry.
type ComponentPolicy struct {
	Paths                []string `yaml:"paths"`
	TestRequires         []string `yaml:"test_requires"`
	VerificationProfiles []string `yaml:"verification_profiles"`
	NetworkBackends      []string `yaml:"network_backends"`
}

// JobPolicy maps a static Zuul job to the part of a CI plan it can execute.
// Backend jobs consume a matching deployment variant. Profile jobs run when
// any listed verification profile is requested.
type JobPolicy struct {
	Scenario                       string   `yaml:"scenario"`
	NetworkBackend                 string   `yaml:"network_backend"`
	VerificationProfiles           []string `yaml:"verification_profiles"`
	SkipIfOnlyVerificationProfiles []string `yaml:"skip_if_only_verification_profiles"`
}

// Match explains why one changed path affected the plan.
type Match struct {
	Path    string   `json:"path"`
	Rule    string   `json:"rule"`
	Action  string   `json:"action"`
	Targets []string `json:"targets,omitempty"`
}

// Variant is the deployment closure for one network backend.
type Variant struct {
	NetworkBackend    string            `json:"network_backend"`
	DependencyOptions map[string]string `json:"dependency_options"`
	Components        []string          `json:"components"`
}

// JobPlan is the executable decision for one static Zuul Molecule job.
type JobPlan struct {
	Name                 string   `json:"name"`
	Scenario             string   `json:"scenario"`
	Run                  bool     `json:"run"`
	NetworkBackend       string   `json:"network_backend,omitempty"`
	Components           []string `json:"components,omitempty"`
	VerificationProfiles []string `json:"verification_profiles,omitempty"`
	Reason               string   `json:"reason"`
}

// Plan is both machine-readable CI input and an explainable build artifact.
type Plan struct {
	Mode                 string    `json:"mode"`
	Changes              []Change  `json:"changes"`
	Matches              []Match   `json:"matches"`
	Targets              []string  `json:"targets,omitempty"`
	DeploymentRoots      []string  `json:"deployment_roots,omitempty"`
	VerificationProfiles []string  `json:"verification_profiles,omitempty"`
	Variants             []Variant `json:"variants,omitempty"`
	Jobs                 []JobPlan `json:"jobs"`
	Reasons              []string  `json:"reasons,omitempty"`
}

const (
	ActionIgnore  = "ignore"
	ActionFull    = "full"
	ActionTargets = "targets"

	ModeNoop      = "noop"
	ModeSelective = "selective"
	ModeFull      = "full"
)
