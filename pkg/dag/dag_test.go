package dag

import (
	"context"
	"errors"
	"fmt"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestAddNode(t *testing.T) {
	g := NewGraph[string]()
	if err := g.AddNode("a", "A"); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if err := g.AddNode("a", "A2"); err == nil {
		t.Fatal("expected error for duplicate node, got nil")
	}
}

func TestAddEdge(t *testing.T) {
	g := NewGraph[string]()
	_ = g.AddNode("a", "A")

	if err := g.AddEdge("a", "missing"); err == nil {
		t.Fatal("expected error for missing target node")
	}
	if err := g.AddEdge("missing", "a"); err == nil {
		t.Fatal("expected error for missing source node")
	}

	_ = g.AddNode("b", "B")
	if err := g.AddEdge("a", "b"); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestWaves_Simple(t *testing.T) {
	// Diamond: A depends on B and C; B and C depend on D.
	g := NewGraph[string]()
	for _, id := range []string{"A", "B", "C", "D"} {
		_ = g.AddNode(id, id)
	}
	_ = g.AddEdge("A", "B")
	_ = g.AddEdge("A", "C")
	_ = g.AddEdge("B", "D")
	_ = g.AddEdge("C", "D")

	waves, err := g.Waves()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(waves) != 3 {
		t.Fatalf("expected 3 waves, got %d: %v", len(waves), waves)
	}

	// Wave 0: D (no deps), Wave 1: B and C, Wave 2: A
	if waves[0][0] != "D" {
		t.Errorf("wave 0: expected [D], got %v", waves[0])
	}
	w1 := sortedCopy(waves[1])
	if len(w1) != 2 || w1[0] != "B" || w1[1] != "C" {
		t.Errorf("wave 1: expected [B C], got %v", w1)
	}
	if waves[2][0] != "A" {
		t.Errorf("wave 2: expected [A], got %v", waves[2])
	}
}

func TestWaves_Linear(t *testing.T) {
	// A → B → C (A depends on B, B depends on C)
	g := NewGraph[string]()
	for _, id := range []string{"A", "B", "C"} {
		_ = g.AddNode(id, id)
	}
	_ = g.AddEdge("A", "B")
	_ = g.AddEdge("B", "C")

	waves, err := g.Waves()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(waves) != 3 {
		t.Fatalf("expected 3 waves, got %d", len(waves))
	}
	for i, w := range waves {
		if len(w) != 1 {
			t.Errorf("wave %d: expected 1 node, got %d", i, len(w))
		}
	}
}

func TestWaves_Parallel(t *testing.T) {
	// A, B, C with no edges → all in one wave
	g := NewGraph[string]()
	for _, id := range []string{"A", "B", "C"} {
		_ = g.AddNode(id, id)
	}

	waves, err := g.Waves()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(waves) != 1 {
		t.Fatalf("expected 1 wave, got %d", len(waves))
	}
	if len(waves[0]) != 3 {
		t.Errorf("expected 3 nodes in wave, got %d", len(waves[0]))
	}
}

func TestWaves_Cycle(t *testing.T) {
	g := NewGraph[string]()
	_ = g.AddNode("A", "A")
	_ = g.AddNode("B", "B")
	_ = g.AddEdge("A", "B")
	_ = g.AddEdge("B", "A")

	_, err := g.Waves()
	if err == nil {
		t.Fatal("expected cycle error, got nil")
	}
	if !strings.Contains(err.Error(), "cycle") {
		t.Errorf("expected cycle in error message, got: %v", err)
	}
}

func TestSubgraph(t *testing.T) {
	g := NewGraph[string]()
	for _, id := range []string{"A", "B", "C", "D"} {
		_ = g.AddNode(id, id)
	}
	_ = g.AddEdge("A", "B")
	_ = g.AddEdge("B", "C")
	_ = g.AddEdge("C", "D")

	sub, err := g.Subgraph([]string{"A", "B", "C"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// Subgraph should have 3 nodes and preserve A→B and B→C edges,
	// but not C→D since D is not in the subgraph.
	if len(sub.nodes) != 3 {
		t.Errorf("expected 3 nodes, got %d", len(sub.nodes))
	}

	waves, err := sub.Waves()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	// C (no deps in sub), then B, then A → 3 waves
	if len(waves) != 3 {
		t.Fatalf("expected 3 waves in subgraph, got %d: %v", len(waves), waves)
	}
}

func TestSubgraph_MissingNode(t *testing.T) {
	g := NewGraph[string]()
	_ = g.AddNode("A", "A")

	_, err := g.Subgraph([]string{"A", "Z"})
	if err == nil {
		t.Fatal("expected error for missing node, got nil")
	}
}

func TestRun_Parallel(t *testing.T) {
	// Three independent nodes should run concurrently.
	g := NewGraph[string]()
	for _, id := range []string{"A", "B", "C"} {
		_ = g.AddNode(id, id)
	}

	var maxConcurrent atomic.Int64
	var current atomic.Int64

	err := g.Run(context.Background(), 0, func(_ context.Context, _ string, _ string) error {
		cur := current.Add(1)
		for {
			old := maxConcurrent.Load()
			if cur <= old || maxConcurrent.CompareAndSwap(old, cur) {
				break
			}
		}
		time.Sleep(50 * time.Millisecond)
		current.Add(-1)
		return nil
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if maxConcurrent.Load() < 2 {
		t.Errorf("expected concurrent execution, max concurrent was %d", maxConcurrent.Load())
	}
}

func TestRun_Error(t *testing.T) {
	// Wave 0: A (succeeds), Wave 1: B (fails), Wave 2: C (should not run)
	g := NewGraph[string]()
	for _, id := range []string{"A", "B", "C"} {
		_ = g.AddNode(id, id)
	}
	_ = g.AddEdge("C", "B")
	_ = g.AddEdge("B", "A")

	boom := errors.New("boom")
	var ran sync.Map

	err := g.Run(context.Background(), 0, func(_ context.Context, id string, _ string) error {
		ran.Store(id, true)
		if id == "B" {
			return boom
		}
		return nil
	})
	if !errors.Is(err, boom) {
		t.Fatalf("expected boom error, got: %v", err)
	}
	if _, ok := ran.Load("C"); ok {
		t.Error("node C should not have run after B failed")
	}
}

func TestRun_Ordering(t *testing.T) {
	// A depends on B depends on C. Execution order must be C, B, A.
	g := NewGraph[string]()
	for _, id := range []string{"A", "B", "C"} {
		_ = g.AddNode(id, id)
	}
	_ = g.AddEdge("A", "B")
	_ = g.AddEdge("B", "C")

	var mu sync.Mutex
	var order []string

	err := g.Run(context.Background(), 1, func(_ context.Context, id string, _ string) error {
		mu.Lock()
		order = append(order, id)
		mu.Unlock()
		return nil
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	expected := "C,B,A"
	got := fmt.Sprintf("%s,%s,%s", order[0], order[1], order[2])
	if got != expected {
		t.Errorf("expected order %s, got %s", expected, got)
	}
}

func sortedCopy(s []string) []string {
	c := make([]string, len(s))
	copy(c, s)
	sort.Strings(c)
	return c
}

// TestRunShortNodeNotBlockedByUnrelatedLongNode asserts the event-driven
// scheduler lets a short node start as soon as its own deps are done, even
// if another (unrelated) node in the same Kahn wave is still running.
func TestRunShortNodeNotBlockedByUnrelatedLongNode(t *testing.T) {
g := NewGraph[string]()
for _, n := range []string{"root", "long", "short_dep", "short"} {
_ = g.AddNode(n, n)
}
// Both "long" and "short_dep" depend on "root" -> same wave.
_ = g.AddEdge("long", "root")
_ = g.AddEdge("short_dep", "root")
// "short" depends on "short_dep" only; it is in the next wave, but its
// single dep completes quickly. Under wave-barrier scheduling it would
// still wait for "long" to finish.
_ = g.AddEdge("short", "short_dep")

var longEnd, shortStart time.Time
var mu sync.Mutex

err := g.Run(context.Background(), 0, func(_ context.Context, id string, _ string) error {
switch id {
case "long":
time.Sleep(200 * time.Millisecond)
mu.Lock()
longEnd = time.Now()
mu.Unlock()
case "short_dep":
time.Sleep(20 * time.Millisecond)
case "short":
mu.Lock()
shortStart = time.Now()
mu.Unlock()
}
return nil
})
if err != nil {
t.Fatalf("unexpected error: %v", err)
}

mu.Lock()
defer mu.Unlock()
if shortStart.IsZero() || longEnd.IsZero() {
t.Fatal("timestamps not captured")
}
// "short" must start before "long" ends; otherwise we still have a
// wave barrier.
if !shortStart.Before(longEnd) {
t.Errorf("short started at %v, expected before longEnd %v (wave barrier still in effect)",
shortStart, longEnd)
}
}

// TestRunStopsDependentsOnError asserts that when a node fails, nodes that
// (transitively) depend on it are cancelled via context instead of hanging.
func TestRunStopsDependentsOnError(t *testing.T) {
g := NewGraph[string]()
for _, n := range []string{"a", "b", "c"} {
_ = g.AddNode(n, n)
}
_ = g.AddEdge("b", "a")
_ = g.AddEdge("c", "b")

var ran atomic.Int32
wantErr := errors.New("boom")

err := g.Run(context.Background(), 0, func(ctx context.Context, id string, _ string) error {
ran.Add(1)
if id == "a" {
return wantErr
}
// b and c should never reach here.
return nil
})
if !errors.Is(err, wantErr) {
t.Fatalf("expected wantErr, got %v", err)
}
if ran.Load() != 1 {
t.Errorf("expected only 'a' to run, got %d runs", ran.Load())
}
_ = strings.TrimSpace // keep strings import used if trimmed in future
}

// TestRunConcurrencyCap asserts the global concurrency cap limits in-flight
// nodes across the whole graph (not just within one wave).
func TestRunConcurrencyCap(t *testing.T) {
g := NewGraph[string]()
// 5 independent nodes — all roots, all ready at once.
for _, n := range []string{"a", "b", "c", "d", "e"} {
_ = g.AddNode(n, n)
}

var inflight, peak atomic.Int32
err := g.Run(context.Background(), 2, func(_ context.Context, _ string, _ string) error {
cur := inflight.Add(1)
for {
p := peak.Load()
if cur <= p || peak.CompareAndSwap(p, cur) {
break
}
}
time.Sleep(30 * time.Millisecond)
inflight.Add(-1)
return nil
})
if err != nil {
t.Fatalf("unexpected error: %v", err)
}
if peak.Load() > 2 {
t.Errorf("expected peak in-flight <= 2, got %d", peak.Load())
}
}
