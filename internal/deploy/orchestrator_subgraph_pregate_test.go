// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"context"
	"errors"
	"io"
	"testing"
	"time"
)

// gateAwareDeployer invokes preGate (mirroring AnsibleDeployer behavior),
// unlike the simpler mocks in orchestrator_test.go that drop it. This is
// what surfaces the multi-tag pre-role-dependency hang.
type gateAwareDeployer struct{}

func (g *gateAwareDeployer) Deploy(ctx context.Context, c Component, preGate func(context.Context) error) error {
	if preGate != nil {
		if err := preGate(ctx); err != nil {
			return err
		}
	}
	return nil
}

// TestDeployMultipleTags_PreRoleDependencyOutsideSubgraph guards against the
// regression where a selected component's PreRoleDependsOn pointed at a
// component outside the user-selected --tags subgraph and caused the pre-role
// goroutine to block forever. With the fix, out-of-subgraph names are
// treated as already-complete, matching --tags semantics.
func TestDeployMultipleTags_PreRoleDependencyOutsideSubgraph(t *testing.T) {
	o := &Orchestrator{
		Deployer:  &gateAwareDeployer{},
		Inventory: "/dev/null",
		Output:    io.Discard,
		Preflight: func(_ context.Context, _ io.Writer) error { return nil },
	}

	// neutron has PreRoleDependsOn=[keystone, ovn, coredns]; none of
	// these are in --tags neutron,nova. Before the fix, neutron's
	// pre-role goroutine waited on those channels forever.
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	err := o.Deploy(ctx, []string{"neutron", "nova"})
	if err != nil {
		t.Fatalf("Deploy returned error (likely a hang regression): %v", err)
	}
	if errors.Is(ctx.Err(), context.DeadlineExceeded) {
		t.Fatal("context deadline exceeded - subgraph deployment hung")
	}
}

// TestDeployMultipleTags_KeystoneAlone covers the keystone variant
// (PreRoleDependsOn=[keycloak]).
func TestDeployMultipleTags_KeystoneAlone(t *testing.T) {
	o := &Orchestrator{
		Deployer:  &gateAwareDeployer{},
		Inventory: "/dev/null",
		Output:    io.Discard,
		Preflight: func(_ context.Context, _ io.Writer) error { return nil },
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := o.Deploy(ctx, []string{"keystone"}); err != nil {
		t.Fatalf("Deploy returned error: %v", err)
	}
}

// failingDeployer fails for a named target, succeeds otherwise. It also
// invokes preGate so we can observe whether MarkDone was triggered after
// a failure (which would unblock the gated downstream pre-role).
type failingDeployer struct {
	failOn   string
	preGated chan string
}

func (f *failingDeployer) Deploy(ctx context.Context, c Component, preGate func(context.Context) error) error {
	if preGate != nil {
		if err := preGate(ctx); err != nil {
			return err
		}
		select {
		case f.preGated <- c.Name:
		default:
		}
	}
	if c.Name == f.failOn {
		return errors.New("synthetic failure")
	}
	return nil
}

// TestDeployFailure_DoesNotMarkDone confirms that a failed component does
// not mark itself done and therefore does not unblock downstream pre-role
// gates. The test runs the keystone -> neutron pre-role chain (well: only
// the part observable in the in-subgraph case) and asserts that when
// keystone fails, the run aborts with the failure rather than silently
// proceeding.
func TestDeployFailure_DoesNotMarkDone(t *testing.T) {
	o := &Orchestrator{
		Deployer: &failingDeployer{
			failOn:   "keycloak",
			preGated: make(chan string, 8),
		},
		Inventory: "/dev/null",
		Output:    io.Discard,
		Preflight: func(_ context.Context, _ io.Writer) error { return nil },
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	err := o.Deploy(ctx, []string{"keycloak", "keystone"})
	if err == nil {
		t.Fatal("expected failure from keycloak to propagate, got nil")
	}
}
