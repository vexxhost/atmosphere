// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package ciplan

import (
	"os"
	"slices"
	"strings"
	"testing"

	"github.com/goccy/go-yaml"
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

func jobForName(t *testing.T, plan Plan, name string) JobPlan {
	t.Helper()
	for _, job := range plan.Jobs {
		if job.Name == name {
			return job
		}
	}
	t.Fatalf("plan does not contain job %q: %#v", name, plan.Jobs)
	return JobPlan{}
}

func TestZuulSelectiveJobsMatchPolicy(t *testing.T) {
	configData, err := os.ReadFile("../../ci/molecule-plan.yaml")
	if err != nil {
		t.Fatalf("reading planner configuration: %v", err)
	}
	config, err := ParseConfig(configData)
	if err != nil {
		t.Fatalf("parsing planner configuration: %v", err)
	}

	zuulData, err := os.ReadFile("../../.zuul.yaml")
	if err != nil {
		t.Fatalf("reading Zuul configuration: %v", err)
	}
	var entries []struct {
		Job struct {
			Name string         `yaml:"name"`
			Vars map[string]any `yaml:"vars"`
		} `yaml:"job"`
	}
	if err := yaml.Unmarshal(zuulData, &entries); err != nil {
		t.Fatalf("parsing Zuul configuration: %v", err)
	}

	configuredJobs := make([]string, 0, len(config.Jobs))
	for name := range config.Jobs {
		configuredJobs = append(configuredJobs, name)
	}
	slices.Sort(configuredJobs)

	var zuulJobs []string
	for _, entry := range entries {
		if entry.Job.Vars == nil {
			continue
		}
		name, ok := entry.Job.Vars["atmosphere_ci_job"].(string)
		if !ok {
			continue
		}
		if !strings.HasSuffix(entry.Job.Name, "-selective") {
			t.Errorf("selective policy job %q uses unexpected Zuul job %q", name, entry.Job.Name)
		}
		zuulJobs = append(zuulJobs, name)
	}
	slices.Sort(zuulJobs)

	if !slices.Equal(zuulJobs, configuredJobs) {
		t.Fatalf("Zuul policy jobs = %v, want %v", zuulJobs, configuredJobs)
	}
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

	for _, name := range []string{"aio-openvswitch", "keycloak"} {
		if job := jobForName(t, plan, name); !job.Run {
			t.Errorf("Keystone plan skips required job %q: %#v", name, job)
		}
	}
	for _, name := range []string{"aio-ovn", "csi-local-path-provisioner", "csi-rbd"} {
		if job := jobForName(t, plan, name); job.Run {
			t.Errorf("Keystone plan unexpectedly runs job %q: %#v", name, job)
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

	if job := jobForName(t, plan, "aio-openvswitch"); !job.Run {
		t.Errorf("Manila plan skips canonical AIO job: %#v", job)
	}
	if job := jobForName(t, plan, "aio-ovn"); job.Run {
		t.Errorf("Manila plan unexpectedly runs OVN AIO job: %#v", job)
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

	if job := jobForName(t, plan, "aio-openvswitch"); !job.Run {
		t.Errorf("Magnum plan skips canonical AIO job: %#v", job)
	}
	for _, name := range []string{
		"aio-ovn",
		"csi-local-path-provisioner",
		"csi-rbd",
		"keycloak",
	} {
		if job := jobForName(t, plan, name); job.Run {
			t.Errorf("Magnum plan unexpectedly runs job %q: %#v", name, job)
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
	for _, name := range []string{"aio-openvswitch", "aio-ovn"} {
		if job := jobForName(t, plan, name); !job.Run {
			t.Errorf("Neutron plan skips required backend job %q: %#v", name, job)
		}
	}
}

func TestPlanCSIRunsOnlyDedicatedScenarios(t *testing.T) {
	plan := planForPath(t, "roles/ceph_csi_rbd/tasks/main.yml")

	for _, name := range []string{"csi-local-path-provisioner", "csi-rbd"} {
		if job := jobForName(t, plan, name); !job.Run {
			t.Errorf("CSI plan skips dedicated job %q: %#v", name, job)
		}
	}
	for _, name := range []string{"aio-openvswitch", "aio-ovn", "keycloak"} {
		if job := jobForName(t, plan, name); job.Run {
			t.Errorf("CSI plan unexpectedly runs job %q: %#v", name, job)
		}
	}
}

func TestPlanIgnoredFilesIsNoop(t *testing.T) {
	plan := planForPath(t, "doc/source/deploy/parallel.rst")
	if plan.Mode != ModeNoop {
		t.Fatalf("mode = %q, want noop: %#v", plan.Mode, plan)
	}
	for _, job := range plan.Jobs {
		if job.Run {
			t.Errorf("noop plan unexpectedly runs job %q: %#v", job.Name, job)
		}
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
	for _, job := range plan.Jobs {
		if !job.Run {
			t.Errorf("full fallback skips job %q: %#v", job.Name, job)
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
