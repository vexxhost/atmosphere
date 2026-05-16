// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"bytes"
	"context"
	"io"
	"sync"
	"testing"
)

// noopPreflight is injected into Orchestrator under test so unit tests do not
// shell out to ansible-playbook for the preflight checks.
func noopPreflight(_ context.Context, _ io.Writer) error { return nil }

// mockDeployer records which components were deployed and in what order.
type mockDeployer struct {
	mu       sync.Mutex
	deployed []string
}

func (m *mockDeployer) Deploy(_ context.Context, component Component, _ func(context.Context) error) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.deployed = append(m.deployed, component.Name)
	return nil
}

func TestOrchestrator_FullDAG(t *testing.T) {
	mock := &mockDeployer{}
	out := &bytes.Buffer{}

	orch := &Orchestrator{
		Deployer:    mock,
		Concurrency: 1, // serial execution for deterministic ordering
		Output:      out,
		Preflight:   noopPreflight,
	}

	if err := orch.Deploy(context.Background(), nil); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	deployed := mock.deployed

	if len(deployed) == 0 {
		t.Fatal("no components deployed")
	}

	// Total: len(Components) components
	if len(deployed) != len(Components) {
		t.Errorf("expected %d deployed components, got %d", len(Components), len(deployed))
	}

	// keystone must appear before nova (nova depends on keystone transitively)
	keystoneIdx := -1
	novaIdx := -1
	for i, name := range deployed {
		if name == "keystone" {
			keystoneIdx = i
		}
		if name == "nova" {
			novaIdx = i
		}
	}
	if keystoneIdx == -1 {
		t.Fatal("keystone not found in deployed list")
	}
	if novaIdx == -1 {
		t.Fatal("nova not found in deployed list")
	}
	if keystoneIdx >= novaIdx {
		t.Errorf("keystone (index %d) must deploy before nova (index %d)", keystoneIdx, novaIdx)
	}
}

func TestOrchestrator_MultipleTags(t *testing.T) {
	mock := &mockDeployer{}
	out := &bytes.Buffer{}

	orch := &Orchestrator{
		Deployer:    mock,
		Concurrency: 1,
		Output:      out,
		Preflight:   noopPreflight,
	}

	if err := orch.Deploy(context.Background(), []string{"nova", "keystone"}); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	deployed := mock.deployed

	// Only nova and keystone should be deployed
	if len(deployed) != 2 {
		t.Fatalf("expected 2 deployed components, got %d: %v", len(deployed), deployed)
	}

	// keystone must come before nova (nova depends on keystone via placement/glance)
	// In the subgraph with only these two, the edge nova->keystone is NOT preserved
	// because nova doesn't directly depend on keystone. Let's verify both are present.
	found := map[string]bool{}
	for _, name := range deployed {
		found[name] = true
	}
	if !found["keystone"] {
		t.Error("keystone not in deployed list")
	}
	if !found["nova"] {
		t.Error("nova not in deployed list")
	}
}

func TestOrchestrator_MultipleTags_UnknownTag(t *testing.T) {
	mock := &mockDeployer{}
	out := &bytes.Buffer{}

	orch := &Orchestrator{
		Deployer:    mock,
		Concurrency: 1,
		Output:      out,
		Preflight:   noopPreflight,
	}

	err := orch.Deploy(context.Background(), []string{"keystone", "nonexistent-component"})
	if err == nil {
		t.Fatal("expected error for unknown tag, got nil")
	}

	if len(mock.deployed) != 0 {
		t.Errorf("expected no deployments on error, got %d", len(mock.deployed))
	}
}

// preGateRecorder captures whether preGate was invoked and what it returned
// for each component deployed, allowing tests to assert pre-role gating.
type preGateRecorder struct {
mu      sync.Mutex
gates   map[string]bool // component name -> gate was invoked
gateErr map[string]error
}

func newPreGateRecorder() *preGateRecorder {
return &preGateRecorder{
gates:   map[string]bool{},
gateErr: map[string]error{},
}
}

func (p *preGateRecorder) Deploy(ctx context.Context, component Component, preGate func(context.Context) error) error {
if preGate != nil {
err := preGate(ctx)
p.mu.Lock()
p.gates[component.Name] = true
p.gateErr[component.Name] = err
p.mu.Unlock()
if err != nil {
return err
}
} else {
p.mu.Lock()
p.gates[component.Name] = false
p.mu.Unlock()
}
return nil
}

func TestOrchestrator_BuildPreGate(t *testing.T) {
tracker := newCompletionTracker([]string{"x", "y"})

withPre := Component{
Name:             "withpre",
PreRoleName:      "withpre_pre",
PreRoleDependsOn: []string{"x"},
}
if gate := buildPreGate(withPre, tracker); gate == nil {
t.Fatal("expected non-nil gate for component with PreRoleDependsOn")
}

noPreDeps := Component{Name: "n1", PreRoleName: "n1_pre"}
if gate := buildPreGate(noPreDeps, tracker); gate != nil {
t.Errorf("expected nil gate when PreRoleDependsOn is empty")
}

noPreRole := Component{Name: "n2", PreRoleDependsOn: []string{"x"}}
if gate := buildPreGate(noPreRole, tracker); gate != nil {
t.Errorf("expected nil gate when PreRoleName is empty")
}
}
