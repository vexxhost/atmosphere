// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package ciplan

import (
	"os"
	"slices"
	"strings"
	"testing"

	"github.com/vexxhost/atmosphere/internal/deploy"
)

func testPlanner(t *testing.T) *Planner {
	t.Helper()

	data, err := os.ReadFile("../../ci/molecule-plan.yaml")
	if err != nil {
		t.Fatalf("reading planner configuration: %v", err)
	}
	config, err := ParseConfig(data)
	if err != nil {
		t.Fatalf("parsing planner configuration: %v", err)
	}
	planner, err := New(config)
	if err != nil {
		t.Fatalf("creating planner: %v", err)
	}
	return planner
}

func planForPath(t *testing.T, changedPath string) Plan {
	t.Helper()
	plan, err := testPlanner(t).Plan([]Change{{Status: "M", Path: changedPath}})
	if err != nil {
		t.Fatalf("planning %q: %v", changedPath, err)
	}
	return plan
}

func TestPlanKeystoneUsesSmallLocalPathClosure(t *testing.T) {
	plan := planForPath(t, "roles/keystone/tasks/main.yml")

	if plan.Mode != ModeSelective {
		t.Fatalf("mode = %q, want selective", plan.Mode)
	}
	if !slices.Equal(plan.Targets, []string{"keystone"}) {
		t.Fatalf("targets = %v, want keystone", plan.Targets)
	}
	if len(plan.Variants) != 1 {
		t.Fatalf("variants = %d, want 1", len(plan.Variants))
	}

	components := plan.Variants[0].Components
	for _, required := range []string{
		"cluster-issuer",
		"csi",
		"keycloak",
		"keystone",
		"kubernetes",
		"percona-xtradb-cluster",
	} {
		if !slices.Contains(components, required) {
			t.Errorf("Keystone closure is missing %q: %v", required, components)
		}
	}
	for _, excluded := range []string{"ceph", "glance", "nova", "neutron", "manila", "magnum"} {
		if slices.Contains(components, excluded) {
			t.Errorf("Keystone closure unexpectedly contains %q: %v", excluded, components)
		}
	}
}

func TestPlanManilaIncludesFunctionalDependencies(t *testing.T) {
	plan := planForPath(t, "charts/patches/manila/0001-example.patch")
	components := plan.Variants[0].Components

	for _, required := range []string{
		"ceph",
		"cinder",
		"glance",
		"keystone",
		"manila",
		"neutron",
		"nova",
		"placement",
	} {
		if !slices.Contains(components, required) {
			t.Errorf("Manila closure is missing %q: %v", required, components)
		}
	}
	for _, excluded := range []string{
		"barbican",
		"heat",
		"horizon",
		"magnum",
		"octavia",
		"openstack-exporter",
	} {
		if slices.Contains(components, excluded) {
			t.Errorf("Manila closure unexpectedly contains %q: %v", excluded, components)
		}
	}
}

func TestPlanMagnumUsesBroadTestEnvironment(t *testing.T) {
	plan := planForPath(t, "roles/magnum/tasks/main.yml")
	components := plan.Variants[0].Components

	for _, required := range []string{
		"barbican",
		"cinder",
		"glance-images",
		"heat",
		"magnum",
		"neutron",
		"nova",
		"octavia",
	} {
		if !slices.Contains(components, required) {
			t.Errorf("Magnum closure is missing %q: %v", required, components)
		}
	}
	for _, excluded := range []string{"horizon", "manila", "openstack-exporter"} {
		if slices.Contains(components, excluded) {
			t.Errorf("Magnum closure unexpectedly contains %q: %v", excluded, components)
		}
	}
}

func TestPlanNeutronCreatesBackendSpecificVariants(t *testing.T) {
	plan := planForPath(t, "roles/neutron/tasks/main.yml")
	if len(plan.Variants) != 2 {
		t.Fatalf("variants = %d, want 2: %#v", len(plan.Variants), plan.Variants)
	}

	var openvswitch, ovn *Variant
	for index := range plan.Variants {
		switch plan.Variants[index].NetworkBackend {
		case "openvswitch":
			openvswitch = &plan.Variants[index]
		case "ovn":
			ovn = &plan.Variants[index]
		}
	}
	if openvswitch == nil || ovn == nil {
		t.Fatalf("expected Open vSwitch and OVN variants: %#v", plan.Variants)
	}
	if !slices.Contains(openvswitch.Components, "coredns") {
		t.Errorf("Open vSwitch variant is missing CoreDNS: %v", openvswitch.Components)
	}
	if slices.Contains(openvswitch.Components, "ovn") {
		t.Errorf("Open vSwitch variant unexpectedly contains OVN: %v", openvswitch.Components)
	}
	if !slices.Contains(ovn.Components, "ovn") {
		t.Errorf("OVN variant is missing OVN: %v", ovn.Components)
	}
	if slices.Contains(ovn.Components, "coredns") {
		t.Errorf("OVN variant unexpectedly contains CoreDNS: %v", ovn.Components)
	}
}

func TestPlanIgnoredFilesIsNoop(t *testing.T) {
	plan := planForPath(t, "doc/source/deploy/parallel.rst")
	if plan.Mode != ModeNoop {
		t.Fatalf("mode = %q, want noop: %#v", plan.Mode, plan)
	}
}

func TestPlanUnknownPathFallsBackToFull(t *testing.T) {
	plan := planForPath(t, "new-runtime-area/config.yaml")
	if plan.Mode != ModeFull {
		t.Fatalf("mode = %q, want full", plan.Mode)
	}
	if len(plan.Variants) != 2 {
		t.Fatalf("full fallback variants = %d, want 2", len(plan.Variants))
	}
	for _, variant := range plan.Variants {
		if len(variant.Components) != len(deploy.Components) {
			t.Errorf(
				"full fallback has %d components, want %d",
				len(variant.Components),
				len(deploy.Components),
			)
		}
	}
}

func TestPlanEmptyChangeListFallsBackToFull(t *testing.T) {
	plan, err := testPlanner(t).Plan(nil)
	if err != nil {
		t.Fatalf("planning an empty change list: %v", err)
	}
	if plan.Mode != ModeFull {
		t.Fatalf("mode = %q, want full", plan.Mode)
	}
}

func TestPlanPolicyChangeFallsBackToFull(t *testing.T) {
	plan := planForPath(t, "ci/molecule-plan.yaml")
	if plan.Mode != ModeFull {
		t.Fatalf("mode = %q, want full", plan.Mode)
	}
}

func TestPlanRenameEvaluatesOldAndNewPaths(t *testing.T) {
	plan, err := testPlanner(t).Plan([]Change{{
		Status:       "R100",
		PreviousPath: "roles/keystone/tasks/old.yml",
		Path:         "roles/manila/tasks/new.yml",
	}})
	if err != nil {
		t.Fatalf("planning rename: %v", err)
	}
	if !slices.Equal(plan.Targets, []string{"keystone", "manila"}) {
		t.Fatalf("rename targets = %v, want keystone and manila", plan.Targets)
	}
}

func TestParseChangesNameStatus(t *testing.T) {
	changes, err := ParseChanges(strings.NewReader(
		"M\troles/keystone/tasks/main.yml\n" +
			"R100\troles/manila/tasks/old.yml\troles/manila/tasks/new.yml\n",
	))
	if err != nil {
		t.Fatalf("ParseChanges returned an error: %v", err)
	}
	if len(changes) != 2 {
		t.Fatalf("changes = %d, want 2", len(changes))
	}
	if changes[1].PreviousPath != "roles/manila/tasks/old.yml" {
		t.Errorf("unexpected previous path: %#v", changes[1])
	}
}

func TestCompileGlobDoubleStar(t *testing.T) {
	matcher, err := compileGlob("roles/manila/**")
	if err != nil {
		t.Fatalf("compileGlob returned an error: %v", err)
	}
	if !matcher.MatchString("roles/manila/tasks/main.yml") {
		t.Error("double-star glob did not match a nested path")
	}
	if matcher.MatchString("roles/magnum/tasks/main.yml") {
		t.Error("double-star glob matched another role")
	}
}
