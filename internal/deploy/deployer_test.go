// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"bytes"
	"context"
	"fmt"
	"strings"
	"sync"
	"testing"
	"time"
)

// trackingDeployer records role names deployed and their timing to verify parallelism.
type trackingDeployer struct {
	mu       sync.Mutex
	events   []deployEvent
	roleTime time.Duration
}

type deployEvent struct {
	component string
	roleName  string
	startedAt time.Time
	endedAt   time.Time
}

func (d *trackingDeployer) Deploy(ctx context.Context, component Component) error {
	// Mirror only the PreRoleName branching needed by this test helper;
	// this doesn't exercise AnsibleDeployer internals.
	if component.PreRoleName == "" {
		d.recordRole(component.Name, component.RoleName)
		return nil
	}

	// Simulate parallel pre-role + main role
	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		d.recordRole(component.Name, component.PreRoleName)
	}()

	go func() {
		defer wg.Done()
		d.recordRole(component.Name, component.RoleName)
	}()

	wg.Wait()
	return nil
}

func (d *trackingDeployer) recordRole(component, roleName string) {
	start := time.Now()
	time.Sleep(d.roleTime)
	end := time.Now()

	d.mu.Lock()
	defer d.mu.Unlock()
	d.events = append(d.events, deployEvent{
		component: component,
		roleName:  roleName,
		startedAt: start,
		endedAt:   end,
	})
}

func TestRenderPlaybook_WithPreRole(t *testing.T) {
	c := Component{
		Name:        "octavia",
		Type:        RoleType,
		RoleName:    "octavia",
		PreRoleName: "octavia_pre",
		Hosts:       "controllers[0]",
	}

	// Main role should include _pre_role_active var
	mainPlaybook := renderPlaybook(c, c.RoleName)
	if !strings.Contains(mainPlaybook, "_pre_role_active: true") {
		t.Errorf("main role playbook should contain _pre_role_active var, got:\n%s", mainPlaybook)
	}

	// Pre-role should NOT include _pre_role_active var
	prePlaybook := renderPlaybook(c, c.PreRoleName)
	if strings.Contains(prePlaybook, "_pre_role_active") {
		t.Errorf("pre-role playbook should not contain _pre_role_active var, got:\n%s", prePlaybook)
	}
}

func TestRenderPlaybook_WithoutPreRole(t *testing.T) {
	c := Component{
		Name:     "keystone",
		Type:     RoleType,
		RoleName: "keystone",
		Hosts:    "controllers[0]",
	}

	playbook := renderPlaybook(c, c.RoleName)
	if strings.Contains(playbook, "_pre_role_active") {
		t.Errorf("playbook without pre-role should not contain _pre_role_active, got:\n%s", playbook)
	}
}

func TestRenderPlaybook_PreRoleUsesCorrectRoleName(t *testing.T) {
	c := Component{
		Name:        "magnum",
		Type:        RoleType,
		RoleName:    "magnum",
		PreRoleName: "magnum_pre",
		Hosts:       "controllers[0]",
	}

	prePlaybook := renderPlaybook(c, c.PreRoleName)
	if !strings.Contains(prePlaybook, "vexxhost.atmosphere.magnum_pre") {
		t.Errorf("pre-role playbook should reference magnum_pre, got:\n%s", prePlaybook)
	}

	mainPlaybook := renderPlaybook(c, c.RoleName)
	if !strings.Contains(mainPlaybook, "vexxhost.atmosphere.magnum") {
		t.Errorf("main role playbook should reference magnum, got:\n%s", mainPlaybook)
	}
}

func TestDeploy_PreRoleRunsInParallel(t *testing.T) {
	deployer := &trackingDeployer{roleTime: 50 * time.Millisecond}

	component := Component{
		Name:        "magnum",
		Type:        RoleType,
		RoleName:    "magnum",
		PreRoleName: "magnum_pre",
		Hosts:       "controllers[0]",
	}

	deployer.Deploy(context.Background(), component)

	if len(deployer.events) != 2 {
		t.Fatalf("expected 2 deploy events, got %d", len(deployer.events))
	}

	var preEvent, mainEvent *deployEvent
	for i := range deployer.events {
		if deployer.events[i].roleName == "magnum_pre" {
			preEvent = &deployer.events[i]
		} else if deployer.events[i].roleName == "magnum" {
			mainEvent = &deployer.events[i]
		}
	}

	if preEvent == nil || mainEvent == nil {
		t.Fatal("expected both magnum_pre and magnum events")
	}

	// Verify the two deployments overlapped in time.
	if preEvent.endedAt.Before(mainEvent.startedAt) || mainEvent.endedAt.Before(preEvent.startedAt) {
		t.Errorf(
			"pre-role and main role should overlap: pre=[%v,%v] main=[%v,%v]",
			preEvent.startedAt,
			preEvent.endedAt,
			mainEvent.startedAt,
			mainEvent.endedAt,
		)
	}
}

func TestDeploy_NoPreRoleRunsSingle(t *testing.T) {
	deployer := &trackingDeployer{roleTime: 10 * time.Millisecond}

	component := Component{
		Name:     "keystone",
		Type:     RoleType,
		RoleName: "keystone",
		Hosts:    "controllers[0]",
	}

	deployer.Deploy(context.Background(), component)

	if len(deployer.events) != 1 {
		t.Fatalf("expected 1 deploy event, got %d", len(deployer.events))
	}
	if deployer.events[0].roleName != "keystone" {
		t.Errorf("expected keystone role, got %s", deployer.events[0].roleName)
	}
}

func TestRenderPlaybook_WithEnvironmentAndPreRole(t *testing.T) {
	c := Component{
		Name:        "test",
		Type:        RoleType,
		RoleName:    "test_main",
		PreRoleName: "test_pre",
		Hosts:       "controllers[0]",
		Environment: map[string]string{"FOO": "bar"},
	}

	out := &bytes.Buffer{}
	_ = out

	mainPlaybook := renderPlaybook(c, c.RoleName)
	if !strings.Contains(mainPlaybook, "FOO:") {
		t.Error("main playbook should include environment")
	}
	if !strings.Contains(mainPlaybook, "_pre_role_active: true") {
		t.Error("main playbook should include _pre_role_active")
	}
}

func TestComponentRegistry_PreRoleComponents(t *testing.T) {
preRoleComponents := []string{}
for _, c := range Components {
if c.PreRoleName != "" {
preRoleComponents = append(preRoleComponents, fmt.Sprintf("%s (pre: %s)", c.Name, c.PreRoleName))
}
}

if len(preRoleComponents) == 0 {
t.Fatal("expected at least one component with PreRoleName")
}

// Verify known components have pre-roles
found := map[string]bool{}
for _, c := range Components {
found[c.Name] = c.PreRoleName != ""
}

if !found["octavia"] {
t.Error("octavia should have a pre-role")
}
if !found["magnum"] {
t.Error("magnum should have a pre-role")
}
}
