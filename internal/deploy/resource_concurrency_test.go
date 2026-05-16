// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"context"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestResourceCoordinator_CustomConcurrency(t *testing.T) {
	components := []Component{
		{Name: "a", Resources: []string{"k8s-api"}},
		{Name: "b", Resources: []string{"k8s-api"}},
		{Name: "c", Resources: []string{"k8s-api"}},
		{Name: "d", Resources: []string{"k8s-api"}},
	}

	rc := NewResourceCoordinator(components, map[string]int{"k8s-api": 2})
	ctx := context.Background()

	var concurrent int64
	var maxConcurrent int64
	var wg sync.WaitGroup

	for _, comp := range components {
		wg.Add(1)
		go func(c Component) {
			defer wg.Done()
			release, err := rc.Acquire(ctx, c)
			if err != nil {
				t.Errorf("unexpected error: %v", err)
				return
			}
			defer release()

			cur := atomic.AddInt64(&concurrent, 1)
			for {
				old := atomic.LoadInt64(&maxConcurrent)
				if cur <= old || atomic.CompareAndSwapInt64(&maxConcurrent, old, cur) {
					break
				}
			}
			time.Sleep(20 * time.Millisecond)
			atomic.AddInt64(&concurrent, -1)
		}(comp)
	}

	wg.Wait()

	if maxConcurrent != 2 {
		t.Errorf("expected max concurrency of 2 for k8s-api override, got %d", maxConcurrent)
	}
}

func TestResourceCoordinator_DefaultK8sApiCap(t *testing.T) {
	// Without an override, k8s-api should use defaultResourceConcurrency (6).
	// Verify the semaphore's buffered capacity matches.
	components := []Component{{Name: "a", Resources: []string{"k8s-api"}}}
	rc := NewResourceCoordinator(components, nil)

	if got := cap(rc.semas["k8s-api"]); got != 6 {
		t.Errorf("expected default k8s-api cap of 6, got %d", got)
	}
}
