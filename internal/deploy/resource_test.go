package deploy

import (
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestResourceCoordinator_Serializes(t *testing.T) {
	components := []Component{
		{Name: "a", Resources: []string{"apt"}},
		{Name: "b", Resources: []string{"apt"}},
		{Name: "c"},
	}

	rc := NewResourceCoordinator(components)

	var concurrent int64
	var maxConcurrent int64
	var wg sync.WaitGroup

	for _, comp := range components[:2] {
		wg.Add(1)
		go func(c Component) {
			defer wg.Done()
			release := rc.Acquire(c)
			defer release()

			cur := atomic.AddInt64(&concurrent, 1)
			for {
				old := atomic.LoadInt64(&maxConcurrent)
				if cur <= old || atomic.CompareAndSwapInt64(&maxConcurrent, old, cur) {
					break
				}
			}

			time.Sleep(10 * time.Millisecond)
			atomic.AddInt64(&concurrent, -1)
		}(comp)
	}

	wg.Wait()

	if maxConcurrent != 1 {
		t.Errorf("expected max concurrency of 1 for shared resource, got %d", maxConcurrent)
	}
}

func TestResourceCoordinator_NoResource(t *testing.T) {
	components := []Component{
		{Name: "a"},
		{Name: "b"},
	}

	rc := NewResourceCoordinator(components)

	// Acquire/release should be no-ops
	release := rc.Acquire(components[0])
	release()
	release = rc.Acquire(components[1])
	release()
}

func TestResourceCoordinator_DifferentResources(t *testing.T) {
	components := []Component{
		{Name: "a", Resources: []string{"apt"}},
		{Name: "b", Resources: []string{"helm"}},
	}

	rc := NewResourceCoordinator(components)

	var concurrent int64
	var maxConcurrent int64
	var wg sync.WaitGroup

	for _, comp := range components {
		wg.Add(1)
		go func(c Component) {
			defer wg.Done()
			release := rc.Acquire(c)
			defer release()

			cur := atomic.AddInt64(&concurrent, 1)
			for {
				old := atomic.LoadInt64(&maxConcurrent)
				if cur <= old || atomic.CompareAndSwapInt64(&maxConcurrent, old, cur) {
					break
				}
			}

			time.Sleep(10 * time.Millisecond)
			atomic.AddInt64(&concurrent, -1)
		}(comp)
	}

	wg.Wait()

	if maxConcurrent != 2 {
		t.Errorf("expected max concurrency of 2 for different resources, got %d", maxConcurrent)
	}
}
