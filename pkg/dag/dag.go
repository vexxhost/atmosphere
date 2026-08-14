package dag

import (
	"context"
	"fmt"

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

// Run executes fn for every node in topological order, running nodes within
// the same wave concurrently. The concurrency parameter limits the number of
// goroutines per wave; if <= 0 there is no limit. Execution stops on the first
// error.
func (g *Graph[T]) Run(ctx context.Context, concurrency int, fn func(ctx context.Context, id string, value T) error) error {
	waves, err := g.Waves()
	if err != nil {
		return err
	}

	for _, wave := range waves {
		eg, ctx := errgroup.WithContext(ctx)
		if concurrency > 0 {
			eg.SetLimit(concurrency)
		}
		for _, id := range wave {
			val := g.nodes[id]
			eg.Go(func() error {
				return fn(ctx, id, val)
			})
		}
		if err := eg.Wait(); err != nil {
			return err
		}
	}
	return nil
}
