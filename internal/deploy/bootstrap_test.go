// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"context"
	"io"
	"slices"
	"testing"
)

func TestBootstrapComponentNamesKeystoneLocalPath(t *testing.T) {
	components, err := BootstrapComponentNames(
		[]string{"keystone"},
		DependencyOptions{DependencyOptionCSIDriver: "local-path-provisioner"},
	)
	if err != nil {
		t.Fatalf("BootstrapComponentNames returned an error: %v", err)
	}

	for _, expected := range []string{
		"csi",
		"ingress-nginx",
		"keycloak",
		"keystone",
		"kubernetes",
		"memcached",
		"percona-xtradb-cluster",
		"percona-xtradb-cluster-operator",
		"rabbitmq-cluster-operator",
	} {
		if !slices.Contains(components, expected) {
			t.Errorf("expected bootstrap closure to contain %q: %v", expected, components)
		}
	}
	if slices.Contains(components, "ceph") {
		t.Errorf("local-path Keystone closure must not contain Ceph: %v", components)
	}
}

func TestBootstrapComponentNamesCSIDriverDependencies(t *testing.T) {
	tests := []struct {
		name     string
		driver   string
		wantCeph bool
	}{
		{name: "rbd", driver: "rbd", wantCeph: true},
		{name: "local path", driver: "local-path-provisioner", wantCeph: false},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			components, err := BootstrapComponentNames(
				[]string{"csi"},
				DependencyOptions{DependencyOptionCSIDriver: test.driver},
			)
			if err != nil {
				t.Fatalf("BootstrapComponentNames returned an error: %v", err)
			}
			if got := slices.Contains(components, "ceph"); got != test.wantCeph {
				t.Errorf("Ceph presence = %v, want %v: %v", got, test.wantCeph, components)
			}
		})
	}
}

func TestBootstrapComponentNamesNeutronBackendDependencies(t *testing.T) {
	tests := []struct {
		name        string
		backend     string
		want        string
		doesNotWant string
	}{
		{
			name:        "Open vSwitch",
			backend:     "openvswitch",
			want:        "coredns",
			doesNotWant: "ovn",
		},
		{
			name:        "OVN",
			backend:     "ovn",
			want:        "ovn",
			doesNotWant: "coredns",
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			components, err := BootstrapComponentNames(
				[]string{"neutron"},
				DependencyOptions{
					DependencyOptionCSIDriver:      "local-path-provisioner",
					DependencyOptionNetworkBackend: test.backend,
				},
			)
			if err != nil {
				t.Fatalf("BootstrapComponentNames returned an error: %v", err)
			}
			if !slices.Contains(components, "openvswitch") {
				t.Errorf("Neutron closure must contain Open vSwitch: %v", components)
			}
			if !slices.Contains(components, test.want) {
				t.Errorf("expected closure to contain %q: %v", test.want, components)
			}
			if slices.Contains(components, test.doesNotWant) {
				t.Errorf("closure must not contain %q: %v", test.doesNotWant, components)
			}
		})
	}
}

func TestBootstrapComponentNamesUnknownTarget(t *testing.T) {
	if _, err := BootstrapComponentNames([]string{"does-not-exist"}, nil); err == nil {
		t.Fatal("expected an error for an unknown component")
	}
}

func TestOrchestratorWithDependencies(t *testing.T) {
	mock := &mockDeployer{}
	orchestrator := &Orchestrator{
		Deployer:         mock,
		Concurrency:      1,
		Output:           io.Discard,
		Preflight:        noopPreflight,
		WithDependencies: true,
		DependencyOptions: DependencyOptions{
			DependencyOptionCSIDriver: "local-path-provisioner",
		},
	}

	if err := orchestrator.Deploy(context.Background(), []string{"keystone"}); err != nil {
		t.Fatalf("Deploy returned an error: %v", err)
	}

	if !slices.Contains(mock.deployed, "keycloak") {
		t.Errorf("fresh Keystone deployment must include its pre-role dependency: %v", mock.deployed)
	}
	if slices.Contains(mock.deployed, "ceph") {
		t.Errorf("fresh local-path Keystone deployment must not include Ceph: %v", mock.deployed)
	}
}
