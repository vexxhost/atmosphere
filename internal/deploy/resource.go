// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"context"
	"fmt"
)

// ResourceCoordinator manages named semaphores to serialize components that
// share a resource (e.g., "apt" for package management) or cap the parallel
// fan-out to a shared backend (e.g., "k8s-api"). Components declaring the
// same resource respect its concurrency cap; components without shared
// resources remain fully parallel.
type ResourceCoordinator struct {
	semas map[string]chan struct{}
}

// defaultResourceConcurrency returns the default cap for a resource when the
// caller does not override it. Historically every resource was a mutex
// (cap=1); newer resources may be backends we merely want to rate-limit.
var defaultResourceConcurrency = map[string]int{
	// apt: package manager. Must be serialized per host, but we also
	// serialize globally today since components touching apt span all hosts.
	"apt": 1,
	// k8s-api: the Kubernetes apiserver. Cap limits how many Helm/Kubernetes
	// operations run concurrently across heavy OpenStack components, smoothing
	// apiserver load during wave fan-out without serializing fully.
	"k8s-api": 6,
	// keycloak-admin: the Keycloak admin HTTP endpoint. The community.general
	// keycloak_* modules rebuild auth state per call; concurrent realm/client
	// creates race and fail. Serialize globally (cap=1).
	"keycloak-admin": 1,
}

// NewResourceCoordinator builds semaphores for every resource declared across
// the given components. Each resource's capacity is looked up in overrides,
// falling back to defaultResourceConcurrency, and finally to 1 (mutex).
func NewResourceCoordinator(components []Component, overrides map[string]int) *ResourceCoordinator {
	resources := make(map[string]bool)
	for _, c := range components {
		for _, r := range c.Resources {
			resources[r] = true
		}
	}

	semas := make(map[string]chan struct{}, len(resources))
	for r := range resources {
		cap := resourceCapacity(r, overrides)
		semas[r] = make(chan struct{}, cap)
	}

	return &ResourceCoordinator{semas: semas}
}

func resourceCapacity(name string, overrides map[string]int) int {
	if v, ok := overrides[name]; ok && v > 0 {
		return v
	}
	if v, ok := defaultResourceConcurrency[name]; ok && v > 0 {
		return v
	}
	return 1
}

// Acquire blocks until all resources required by the component are available
// or the context is cancelled. Returns a release function and nil on success,
// or a nil function and an error if the context was cancelled while waiting.
func (rc *ResourceCoordinator) Acquire(ctx context.Context, comp Component) (func(), error) {
	if len(comp.Resources) == 0 {
		return func() {}, nil
	}

	acquired := make([]string, 0, len(comp.Resources))
	for _, r := range comp.Resources {
		if ch, ok := rc.semas[r]; ok {
			select {
			case ch <- struct{}{}:
				acquired = append(acquired, r)
			case <-ctx.Done():
				// Release any resources already acquired
				for _, ar := range acquired {
					if ach, ok := rc.semas[ar]; ok {
						<-ach
					}
				}
				return nil, fmt.Errorf("context cancelled waiting for resource %q: %w", r, ctx.Err())
			}
		}
	}

	return func() {
		for _, r := range comp.Resources {
			if ch, ok := rc.semas[r]; ok {
				<-ch
			}
		}
	}, nil
}
