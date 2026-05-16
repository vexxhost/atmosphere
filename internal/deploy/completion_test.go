// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"context"
	"errors"
	"sync/atomic"
	"testing"
	"time"
)

func TestCompletionTracker_WaitBlocksUntilDone(t *testing.T) {
	tr := newCompletionTracker([]string{"a", "b"})

	var waited atomic.Bool
	done := make(chan struct{})
	go func() {
		defer close(done)
		if err := tr.Wait(context.Background(), []string{"a"}); err != nil {
			t.Errorf("unexpected error: %v", err)
			return
		}
		waited.Store(true)
	}()

	// Give the goroutine a chance to block on the channel.
	time.Sleep(20 * time.Millisecond)
	if waited.Load() {
		t.Fatal("Wait returned before MarkDone was called")
	}

	tr.MarkDone("a")
	<-done
	if !waited.Load() {
		t.Fatal("Wait did not return after MarkDone")
	}
}

func TestCompletionTracker_MarkDoneIdempotent(t *testing.T) {
	tr := newCompletionTracker([]string{"a"})
	tr.MarkDone("a")
	tr.MarkDone("a") // must not panic on double close
	if err := tr.Wait(context.Background(), []string{"a"}); err != nil {
		t.Fatalf("Wait on already-done name returned error: %v", err)
	}
}

func TestCompletionTracker_UnknownNameIgnored(t *testing.T) {
	tr := newCompletionTracker([]string{"a"})
	if err := tr.Wait(context.Background(), []string{"unknown"}); err != nil {
		t.Fatalf("Wait on unknown name should be a no-op, got: %v", err)
	}
}

func TestCompletionTracker_ContextCancellation(t *testing.T) {
	tr := newCompletionTracker([]string{"a"})
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	err := tr.Wait(ctx, []string{"a"})
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("expected context.Canceled, got: %v", err)
	}
}
