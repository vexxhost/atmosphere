package deploy

import (
	"context"
	"fmt"
)

// ResourceCoordinator manages named semaphores to serialize components that
// share a resource (e.g., "apt" for package management). Components in the
// same DAG wave that declare the same resource run one at a time, while
// components without shared resources remain fully parallel.
type ResourceCoordinator struct {
	semas map[string]chan struct{}
}

// NewResourceCoordinator builds semaphores for every resource declared across
// the given components. Each resource defaults to a concurrency of 1 (mutex).
func NewResourceCoordinator(components []Component) *ResourceCoordinator {
	resources := make(map[string]bool)
	for _, c := range components {
		for _, r := range c.Resources {
			resources[r] = true
		}
	}

	semas := make(map[string]chan struct{}, len(resources))
	for r := range resources {
		semas[r] = make(chan struct{}, 1)
	}

	return &ResourceCoordinator{semas: semas}
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
