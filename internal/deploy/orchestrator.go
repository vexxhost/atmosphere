package deploy

import (
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"sync"
)

// preflightPlaybook contains validation checks that mirror pre_tasks from the
// original sequential playbooks (e.g., playbooks/openstack.yml). The parallel
// orchestrator generates minimal single-role playbooks for RoleType components,
// which bypasses pre_tasks defined in the original playbook files. Running these
// checks before the DAG ensures configuration errors are caught early.
const preflightPlaybook = `---
- name: Preflight checks
  hosts: controllers[0]
  become: true
  gather_facts: false
  tasks:
    - name: Fail if atmosphere_ceph_enabled is set
      ansible.builtin.fail:
        msg: >-
          The "atmosphere_ceph_enabled" variable is no longer supported.
          Please use the "atmosphere_storage" variable to configure storage
          backends instead. Refer to the storage configuration documentation
          for migration instructions.
      when: atmosphere_ceph_enabled is defined
`

// Orchestrator coordinates the parallel deployment of Atmosphere components.
type Orchestrator struct {
	// Deployer is the deployment backend (e.g., AnsibleDeployer).
	Deployer Deployer
	// Inventory is the path to the Ansible inventory file.
	Inventory string
	// Output is the writer for status messages (defaults to os.Stdout).
	Output io.Writer
	// Concurrency limits parallel deployments per wave (0 = unlimited).
	Concurrency int
	// Preflight is invoked before any component deployment and is expected
	// to return an error if the environment is misconfigured. When nil, the
	// default implementation shells out to ansible-playbook with the
	// preflightPlaybook defined in this file. Tests inject a no-op to
	// keep the unit tests hermetic.
	Preflight func(ctx context.Context, output io.Writer) error
}

// preflight dispatches to a caller-supplied Preflight hook when set, falling
// back to the ansible-playbook-based implementation otherwise.
func (o *Orchestrator) preflight(ctx context.Context, output io.Writer) error {
	if o.Preflight != nil {
		return o.Preflight(ctx, output)
	}
	return o.runPreflightChecks(ctx, output)
}

// Deploy runs the deployment based on the provided tags.
// - No tags: full DAG, all components, parallel waves
// - Single tag: pass-through to ansible-playbook site.yml --tags <tag>
// - Multiple tags: extract subgraph, resolve DAG ordering, parallel waves
func (o *Orchestrator) Deploy(ctx context.Context, tags []string) error {
	output := o.Output
	if output == nil {
		output = os.Stdout
	}

	switch len(tags) {
	case 0:
		return o.deployFullDAG(ctx, output)
	case 1:
		return o.deploySingleTag(ctx, tags[0], output)
	default:
		return o.deployMultipleTags(ctx, tags, output)
	}
}

// runPreflightChecks runs validation checks before any component deployment.
// This ensures that deprecated or invalid configuration is caught early, mirroring
// the pre_tasks from the original sequential playbooks (e.g., playbooks/openstack.yml).
func (o *Orchestrator) runPreflightChecks(ctx context.Context, output io.Writer) error {
	fmt.Fprintln(output, "==> Running preflight checks")

	cmd := exec.CommandContext(ctx, "ansible-playbook", "/dev/stdin",
		"--inventory", o.Inventory)
	cmd.Stdin = strings.NewReader(preflightPlaybook)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("stdout pipe: %w", err)
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("stderr pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("starting preflight checks: %w", err)
	}

	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		prefixOutput("preflight", stdout, output)
	}()
	go func() {
		defer wg.Done()
		prefixOutput("preflight", stderr, output)
	}()
	wg.Wait()

	if err := cmd.Wait(); err != nil {
		return fmt.Errorf("preflight checks failed: %w", err)
	}

	fmt.Fprintln(output, "==> Preflight checks passed")
	return nil
}

// deployFullDAG runs all components in parallel waves.
func (o *Orchestrator) deployFullDAG(ctx context.Context, output io.Writer) error {
	if err := o.preflight(ctx, output); err != nil {
		return err
	}

	g, err := BuildGraph()
	if err != nil {
		return fmt.Errorf("building dependency graph: %w", err)
	}

	rc := NewResourceCoordinator(Components)

	fmt.Fprintln(output, "==> Starting parallel deployment")
	return g.Run(ctx, o.Concurrency, func(ctx context.Context, id string, comp Component) error {
		fmt.Fprintf(output, "==> [%s] Starting deployment\n", id)

		release, err := rc.Acquire(ctx, comp)
		if err != nil {
			return fmt.Errorf("component %s: %w", id, err)
		}
		defer release()

		if err := o.Deployer.Deploy(ctx, comp); err != nil {
			return fmt.Errorf("component %s failed: %w", id, err)
		}
		fmt.Fprintf(output, "==> [%s] Deployment complete\n", id)
		return nil
	})
}

// deploySingleTag passes through to ansible-playbook with the tag.
// This is identical to running: ansible-playbook vexxhost.atmosphere.site --tags <tag>
func (o *Orchestrator) deploySingleTag(ctx context.Context, tag string, output io.Writer) error {
	fmt.Fprintf(output, "==> Single tag mode: %s\n", tag)

	cmd := exec.CommandContext(ctx, "ansible-playbook", "vexxhost.atmosphere.site",
		"--inventory", o.Inventory,
		"--tags", tag)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("stdout pipe: %w", err)
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("stderr pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("starting ansible-playbook: %w", err)
	}

	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		prefixOutput(tag, stdout, output)
	}()
	go func() {
		defer wg.Done()
		prefixOutput(tag, stderr, output)
	}()
	wg.Wait()

	if err := cmd.Wait(); err != nil {
		return fmt.Errorf("ansible-playbook --tags %s failed: %w", tag, err)
	}

	return nil
}

// deployMultipleTags extracts a subgraph for the specified tags and runs them
// in DAG order with parallel waves.
func (o *Orchestrator) deployMultipleTags(ctx context.Context, tags []string, output io.Writer) error {
	fmt.Fprintf(output, "==> Multi-tag mode: %s\n", strings.Join(tags, ", "))

	if err := o.preflight(ctx, output); err != nil {
		return err
	}

	// Resolve tag names to component names
	componentNames := make([]string, 0, len(tags))
	for _, tag := range tags {
		comp, ok := FindComponent(tag)
		if !ok {
			return fmt.Errorf("unknown component or tag: %q", tag)
		}
		componentNames = append(componentNames, comp.Name)
	}

	// Build full graph, then extract subgraph
	fullGraph, err := BuildGraph()
	if err != nil {
		return fmt.Errorf("building dependency graph: %w", err)
	}

	subGraph, err := fullGraph.Subgraph(componentNames)
	if err != nil {
		return fmt.Errorf("extracting subgraph: %w", err)
	}

	rc := NewResourceCoordinator(Components)

	fmt.Fprintln(output, "==> Starting parallel deployment (subgraph)")
	return subGraph.Run(ctx, o.Concurrency, func(ctx context.Context, id string, comp Component) error {
		fmt.Fprintf(output, "==> [%s] Starting deployment\n", id)

		release, err := rc.Acquire(ctx, comp)
		if err != nil {
			return fmt.Errorf("component %s: %w", id, err)
		}
		defer release()

		if err := o.Deployer.Deploy(ctx, comp); err != nil {
			return fmt.Errorf("component %s failed: %w", id, err)
		}
		fmt.Fprintf(output, "==> [%s] Deployment complete\n", id)
		return nil
	})
}
