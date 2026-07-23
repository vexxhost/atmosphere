// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package main

import (
	"fmt"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"github.com/spf13/cobra"
	"github.com/vexxhost/atmosphere/internal/deploy"
)

func newDeployCmd() *cobra.Command {
	var (
		inventory        string
		tags             string
		concurrency      int
		withDependencies bool
		dependencyValues []string
	)

	cmd := &cobra.Command{
		Use:   "deploy",
		Short: "Deploy Atmosphere components",
		Long: `Deploy Atmosphere components using parallel execution.

Without --tags, deploys all components in parallel waves based on the
dependency graph. With a single --tags value, passes through directly
to ansible-playbook for backwards compatibility. With multiple
comma-separated --tags, resolves ordering from the dependency graph
and runs them in parallel where possible.

Use --with-dependencies with one or more tags when bootstrapping a fresh
environment. It expands the selected tags to their complete transitive
dependency closure before deploying them.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			if inventory == "" {
				return fmt.Errorf("--inventory is required")
			}
			if withDependencies && strings.TrimSpace(tags) == "" {
				return fmt.Errorf("--with-dependencies requires --tags")
			}

			dependencyOptions, err := parseDependencyOptions(dependencyValues)
			if err != nil {
				return err
			}

			deployer := &deploy.AnsibleDeployer{
				Inventory: inventory,
				Output:    os.Stdout,
			}

			orchestrator := &deploy.Orchestrator{
				Deployer:          deployer,
				Inventory:         inventory,
				Output:            os.Stdout,
				Concurrency:       concurrency,
				WithDependencies:  withDependencies,
				DependencyOptions: dependencyOptions,
			}

			// Parse tags
			var tagList []string
			if tags != "" {
				tagList = strings.Split(tags, ",")
				for i, t := range tagList {
					tagList[i] = strings.TrimSpace(t)
				}
			}

			// Cancel the context on SIGINT/SIGTERM so in-flight
			// ansible-playbook/helm/ssh subprocesses (started with
			// exec.CommandContext) are torn down instead of being
			// orphaned when the user hits Ctrl-C.
			ctx, stop := signal.NotifyContext(cmd.Context(), os.Interrupt, syscall.SIGTERM)
			defer stop()

			return orchestrator.Deploy(ctx, tagList)
		},
	}

	cmd.Flags().StringVarP(&inventory, "inventory", "i", "", "Path to Ansible inventory file (required)")
	cmd.Flags().StringVarP(&tags, "tags", "t", "", "Comma-separated list of component tags to deploy")
	cmd.Flags().IntVar(&concurrency, "concurrency", 0, "Max concurrent deployments per wave (0 = unlimited)")
	cmd.Flags().BoolVar(&withDependencies, "with-dependencies", false, "Include transitive dependencies needed by a fresh environment")
	cmd.Flags().StringSliceVar(
		&dependencyValues,
		"dependency-option",
		nil,
		"Dependency option in key=value form (for example csi_driver=local-path-provisioner)",
	)

	return cmd
}

func parseDependencyOptions(values []string) (deploy.DependencyOptions, error) {
	options := deploy.DependencyOptions{}
	for _, value := range values {
		key, optionValue, found := strings.Cut(value, "=")
		key = strings.TrimSpace(key)
		optionValue = strings.TrimSpace(optionValue)
		if !found || key == "" || optionValue == "" {
			return nil, fmt.Errorf("invalid dependency option %q: expected key=value", value)
		}
		if _, exists := options[key]; exists {
			return nil, fmt.Errorf("dependency option %q was provided more than once", key)
		}
		options[key] = optionValue
	}
	if err := deploy.ValidateDependencyOptions(options); err != nil {
		return nil, err
	}
	return options, nil
}
