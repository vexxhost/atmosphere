// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package dag

import (
	"container/heap"
	"context"
	"fmt"
	"sync"

	"golang.org/x/sync/errgroup"
)

// Graph is a generic directed acyclic graph where nodes hold values of type T.
// Edges represent dependencies: an edge from A to B means A depends on B.
type Graph[T any] struct {
	nodes   map[string]T
	edges   map[string][]string // node -> nodes it depends on
	reverse map[string][]string // node -> nodes that depend on it
}

// NewGraph creates an empty graph.
func NewGraph[T any]() *Graph[T] {
	return &Graph[T]{
		nodes:   make(map[string]T),
		edges:   make(map[string][]string),
		reverse: make(map[string][]string),
	}
}

// AddNode adds a node with the given ID and value. Returns an error if the ID
// already exists.
func (g *Graph[T]) AddNode(id string, value T) error {
	if _, ok := g.nodes[id]; ok {
		return fmt.Errorf("node %q already exists", id)
	}
	g.nodes[id] = value
	return nil
}

// AddEdge adds a dependency edge indicating that "from" depends on "to".
// Returns an error if either node does not exist.
func (g *Graph[T]) AddEdge(from, to string) error {
	if _, ok := g.nodes[from]; !ok {
		return fmt.Errorf("node %q not found", from)
	}
	if _, ok := g.nodes[to]; !ok {
		return fmt.Errorf("node %q not found", to)
	}
	g.edges[from] = append(g.edges[from], to)
	g.reverse[to] = append(g.reverse[to], from)
	return nil
}

// Waves performs a topological sort using Kahn's algorithm and returns node IDs
// grouped into waves. Nodes within the same wave have no dependencies on each
// other and can be processed concurrently. Returns an error if the graph
// contains a cycle.
func (g *Graph[T]) Waves() ([][]string, error) {
	inDegree := make(map[string]int, len(g.nodes))
	for id := range g.nodes {
		inDegree[id] = len(g.edges[id])
	}

	var queue []string
	for id, deg := range inDegree {
		if deg == 0 {
			queue = append(queue, id)
		}
	}

	var waves [][]string
	visited := 0

	for len(queue) > 0 {
		waves = append(waves, queue)
		visited += len(queue)

		var next []string
		for _, id := range queue {
			for _, dep := range g.reverse[id] {
				inDegree[dep]--
				if inDegree[dep] == 0 {
					next = append(next, dep)
				}
			}
		}
		queue = next
	}

	if visited != len(g.nodes) {
		return nil, fmt.Errorf("cycle detected: visited %d of %d nodes", visited, len(g.nodes))
	}
	return waves, nil
}

// Subgraph extracts a new graph containing only the specified nodes, preserving
// edges between them. Returns an error if any node ID is not found.
func (g *Graph[T]) Subgraph(nodeIDs []string) (*Graph[T], error) {
	sub := NewGraph[T]()
	keep := make(map[string]bool, len(nodeIDs))

	for _, id := range nodeIDs {
		val, ok := g.nodes[id]
		if !ok {
			return nil, fmt.Errorf("node %q not found", id)
		}
		keep[id] = true
		if err := sub.AddNode(id, val); err != nil {
			return nil, err
		}
	}

	for from, deps := range g.edges {
		if !keep[from] {
			continue
		}
		for _, to := range deps {
			if keep[to] {
				if err := sub.AddEdge(from, to); err != nil {
					return nil, err
				}
			}
		}
	}
	return sub, nil
}

// CriticalPath returns, for every node, the length (in unit-weighted node
// count including the node itself) of the longest downstream chain. Leaves
// have a value of 1. The result is stable across calls on the same graph
// and is used by Run to prioritise ready nodes when concurrency is capped:
// starting nodes with more work behind them first shortens the makespan
// under classic list-scheduling (HEFT) heuristics.
func (g *Graph[T]) CriticalPath() map[string]int {
	memo := make(map[string]int, len(g.nodes))
	var visit func(id string) int
	visit = func(id string) int {
		if v, ok := memo[id]; ok {
			return v
		}
		best := 0
		for _, dep := range g.reverse[id] {
			if d := visit(dep); d > best {
				best = d
			}
		}
		memo[id] = best + 1
		return memo[id]
	}
	for id := range g.nodes {
		visit(id)
	}
	return memo
}

// Run executes fn for every node in topological order. Each node starts as
// soon as all of its direct dependencies have completed successfully, without
// waiting for the rest of its topological "wave" to finish. The concurrency
// parameter caps the number of nodes running at the same time across the
// whole graph; if <= 0 there is no limit. Execution stops on the first error:
// nodes already running continue, but dependents of any node (failed or not
// yet started) are cancelled via the context.
//
// When concurrency is bounded and multiple nodes are simultaneously ready to
// run, admission order follows CriticalPath: the ready node with the longest
// downstream chain is admitted first. This reduces tail latency compared to
// the arbitrary FIFO a plain channel semaphore would give.
func (g *Graph[T]) Run(ctx context.Context, concurrency int, fn func(ctx context.Context, id string, value T) error) error {
	if _, err := g.Waves(); err != nil {
		return err
	}

	done := make(map[string]chan struct{}, len(g.nodes))
	for id := range g.nodes {
		done[id] = make(chan struct{})
	}

	var sched *prioScheduler
	if concurrency > 0 {
		sched = newPrioScheduler(concurrency)
		defer sched.stop()
	}

	priorities := g.CriticalPath()

	eg, ctx := errgroup.WithContext(ctx)
	for id, val := range g.nodes {
		id, val := id, val
		eg.Go(func() error {
			for _, dep := range g.edges[id] {
				select {
				case <-done[dep]:
				case <-ctx.Done():
					return ctx.Err()
				}
			}

			if sched != nil {
				if err := sched.acquire(ctx, priorities[id]); err != nil {
					return err
				}
				defer sched.release()
			}

			if err := fn(ctx, id, val); err != nil {
				return err
			}
			close(done[id])
			return nil
		})
	}
	return eg.Wait()
}

// prioScheduler is a priority-aware concurrency limiter. Waiters register
// themselves with a priority; a single scheduler goroutine admits the
// highest-priority waiter whenever capacity becomes available. Ties are
// broken by arrival sequence so ordering remains deterministic under equal
// priorities.
type prioScheduler struct {
	mu       sync.Mutex
	cap      int
	inFlight int
	heap     waiterHeap
	seq      uint64
	wake     chan struct{}
	quit     chan struct{}
}

func newPrioScheduler(capacity int) *prioScheduler {
	s := &prioScheduler{
		cap:  capacity,
		wake: make(chan struct{}, 1),
		quit: make(chan struct{}),
	}
	go s.loop()
	return s
}

func (s *prioScheduler) stop() {
	close(s.quit)
}

func (s *prioScheduler) acquire(ctx context.Context, priority int) error {
	ready := make(chan struct{})
	w := &waiter{priority: priority, ready: ready}

	s.mu.Lock()
	s.seq++
	w.seq = s.seq
	heap.Push(&s.heap, w)
	s.mu.Unlock()
	s.signal()

	select {
	case <-ready:
		return nil
	case <-ctx.Done():
		s.mu.Lock()
		w.cancelled = true
		// If the scheduler already admitted us concurrently, honour it
		// and immediately release so capacity is not leaked.
		select {
		case <-ready:
			s.inFlight--
			s.mu.Unlock()
			s.signal()
		default:
			s.mu.Unlock()
		}
		return ctx.Err()
	}
}

func (s *prioScheduler) release() {
	s.mu.Lock()
	s.inFlight--
	s.mu.Unlock()
	s.signal()
}

func (s *prioScheduler) signal() {
	select {
	case s.wake <- struct{}{}:
	default:
	}
}

func (s *prioScheduler) loop() {
	for {
		select {
		case <-s.quit:
			return
		case <-s.wake:
		}
		s.mu.Lock()
		for s.inFlight < s.cap && s.heap.Len() > 0 {
			w := heap.Pop(&s.heap).(*waiter)
			if w.cancelled {
				continue
			}
			s.inFlight++
			close(w.ready)
		}
		s.mu.Unlock()
	}
}

type waiter struct {
	priority  int
	seq       uint64
	ready     chan struct{}
	cancelled bool
	index     int
}

type waiterHeap []*waiter

func (h waiterHeap) Len() int { return len(h) }

func (h waiterHeap) Less(i, j int) bool {
	if h[i].priority != h[j].priority {
		return h[i].priority > h[j].priority
	}
	return h[i].seq < h[j].seq
}

func (h waiterHeap) Swap(i, j int) {
	h[i], h[j] = h[j], h[i]
	h[i].index = i
	h[j].index = j
}

func (h *waiterHeap) Push(x any) {
	w := x.(*waiter)
	w.index = len(*h)
	*h = append(*h, w)
}

func (h *waiterHeap) Pop() any {
	old := *h
	n := len(old)
	w := old[n-1]
	old[n-1] = nil
	w.index = -1
	*h = old[:n-1]
	return w
}
