package deploy

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"sort"
	"strings"
	"sync"
)

// Deployer deploys a single component.
type Deployer interface {
	Deploy(ctx context.Context, component Component) error
}

// AnsibleDeployer deploys components by spawning ansible-playbook subprocesses.
type AnsibleDeployer struct {
	// Inventory is the path to the Ansible inventory file.
	Inventory string
	// Output is the writer for prefixed output (defaults to os.Stdout).
	Output io.Writer
}

func (a *AnsibleDeployer) Deploy(ctx context.Context, component Component) error {
	output := a.Output
	if output == nil {
		output = os.Stdout
	}

	var cmd *exec.Cmd

	switch component.Type {
	case PlaybookType:
		playbookRef := "vexxhost.atmosphere." + component.Playbook
		cmd = exec.CommandContext(ctx, "ansible-playbook", playbookRef,
			"--inventory", a.Inventory)
	case RoleType:
		playbook := renderPlaybook(component)
		cmd = exec.CommandContext(ctx, "ansible-playbook", "/dev/stdin",
			"--inventory", a.Inventory)
		cmd.Stdin = strings.NewReader(playbook)
	default:
		return fmt.Errorf("unknown component type: %d", component.Type)
	}

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("stdout pipe: %w", err)
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("stderr pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("starting ansible-playbook for %s: %w", component.Name, err)
	}

	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		prefixOutput(component.Name, stdout, output)
	}()
	go func() {
		defer wg.Done()
		prefixOutput(component.Name, stderr, output)
	}()

	wg.Wait()

	if err := cmd.Wait(); err != nil {
		return fmt.Errorf("ansible-playbook failed for %s: %w", component.Name, err)
	}

	return nil
}

func renderPlaybook(c Component) string {
	var b strings.Builder
	b.WriteString("---\n")
	b.WriteString(fmt.Sprintf("- hosts: %s\n", c.Hosts))
	b.WriteString("  become: true\n")

	if c.GatherFacts != nil && !*c.GatherFacts {
		b.WriteString("  gather_facts: false\n")
	}

	if len(c.Environment) > 0 {
		b.WriteString("  environment:\n")
		keys := make([]string, 0, len(c.Environment))
		for k := range c.Environment {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			b.WriteString(fmt.Sprintf("    %s: %q\n", k, c.Environment[k]))
		}
	}

	b.WriteString("  roles:\n")
	roleName := c.RoleName
	if !strings.Contains(roleName, ".") {
		roleName = "vexxhost.atmosphere." + roleName
	}
	b.WriteString(fmt.Sprintf("    - role: %s\n", roleName))
	if c.When != "" {
		b.WriteString(fmt.Sprintf("      when: %q\n", c.When))
	}

	return b.String()
}

func prefixOutput(component string, r io.Reader, w io.Writer) {
	scanner := bufio.NewScanner(r)
	buf := make([]byte, 0, 64*1024)
	scanner.Buffer(buf, 1024*1024)
	for scanner.Scan() {
		fmt.Fprintf(w, "[%s] %s\n", component, scanner.Text())
	}
}
