package deploy

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

// Acquire blocks until all resources required by the component are available,
// then returns a release function that must be called when the work is done.
func (rc *ResourceCoordinator) Acquire(comp Component) func() {
	if len(comp.Resources) == 0 {
		return func() {}
	}

	for _, r := range comp.Resources {
		if ch, ok := rc.semas[r]; ok {
			ch <- struct{}{}
		}
	}

	return func() {
		for _, r := range comp.Resources {
			if ch, ok := rc.semas[r]; ok {
				<-ch
			}
		}
	}
}
