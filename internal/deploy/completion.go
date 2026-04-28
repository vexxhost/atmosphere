// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"context"
	"sync"
)

// completionTracker signals when named components finish deploying. Components
// whose pre-role has an asymmetric dependency (see Component.PreRoleDependsOn)
// use it to gate the pre-role while the main role runs eagerly.
//
// Signals are one-shot: MarkDone is idempotent; Wait returns immediately for
// already-completed names.
type completionTracker struct {
	mu   sync.Mutex
	done map[string]chan struct{}
}

// newCompletionTracker preallocates channels for every component name so that
// Wait can be called before MarkDone without a race.
func newCompletionTracker(names []string) *completionTracker {
	m := make(map[string]chan struct{}, len(names))
	for _, n := range names {
		m[n] = make(chan struct{})
	}
	return &completionTracker{done: m}
}

// MarkDone signals that the component with the given name has finished.
// Safe to call multiple times; only the first call closes the channel.
func (t *completionTracker) MarkDone(name string) {
	t.mu.Lock()
	ch, ok := t.done[name]
	t.mu.Unlock()
	if !ok {
		return
	}
	select {
	case <-ch:
	default:
		close(ch)
	}
}

// Wait blocks until every named component is done or the context is cancelled.
// Unknown names are ignored so the caller does not need to pre-validate them.
func (t *completionTracker) Wait(ctx context.Context, names []string) error {
	for _, n := range names {
		t.mu.Lock()
		ch, ok := t.done[n]
		t.mu.Unlock()
		if !ok {
			continue
		}
		select {
		case <-ch:
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	return nil
}
