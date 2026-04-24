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

func TestResourceCoordinator_Serializes(t *testing.T) {
	components := []Component{
		{Name: "a", Resources: []string{"apt"}},
		{Name: "b", Resources: []string{"apt"}},
		{Name: "c"},
	}

	rc := NewResourceCoordinator(components, nil)
	ctx := context.Background()

	var concurrent int64
	var maxConcurrent int64
	var wg sync.WaitGroup

	for _, comp := range components[:2] {
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

	rc := NewResourceCoordinator(components, nil)
	ctx := context.Background()

	release, err := rc.Acquire(ctx, components[0])
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	release()
	release, err = rc.Acquire(ctx, components[1])
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	release()
}

func TestResourceCoordinator_DifferentResources(t *testing.T) {
	components := []Component{
		{Name: "a", Resources: []string{"apt"}},
		{Name: "b", Resources: []string{"helm"}},
	}

	rc := NewResourceCoordinator(components, nil)
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

			time.Sleep(10 * time.Millisecond)
			atomic.AddInt64(&concurrent, -1)
		}(comp)
	}

	wg.Wait()

	if maxConcurrent != 2 {
		t.Errorf("expected max concurrency of 2 for different resources, got %d", maxConcurrent)
	}
}

func TestResourceCoordinator_ContextCancellation(t *testing.T) {
	components := []Component{
		{Name: "a", Resources: []string{"apt"}},
		{Name: "b", Resources: []string{"apt"}},
	}

	rc := NewResourceCoordinator(components, nil)
	ctx := context.Background()

	// Acquire the resource with component a
	release, err := rc.Acquire(ctx, components[0])
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// Try to acquire with a cancelled context — should fail
	cancelCtx, cancel := context.WithCancel(context.Background())
	cancel()

	_, err = rc.Acquire(cancelCtx, components[1])
	if err == nil {
		t.Fatal("expected error from cancelled context, got nil")
	}

	release()
}
