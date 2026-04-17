package main

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/vexxhost/atmosphere/internal/deploy"
)

func newDeployCmd() *cobra.Command {
	var (
		inventory   string
		tags        string
		concurrency int
		prepull     bool
	)

	cmd := &cobra.Command{
		Use:   "deploy",
		Short: "Deploy Atmosphere components",
		Long: `Deploy Atmosphere components using parallel execution.

Without --tags, deploys all components in parallel waves based on the
dependency graph. With a single --tags value, passes through directly
to ansible-playbook for backwards compatibility. With multiple
comma-separated --tags, resolves ordering from the dependency graph
and runs them in parallel where possible.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			if inventory == "" {
				return fmt.Errorf("--inventory is required")
			}

			deployer := &deploy.AnsibleDeployer{
				Inventory: inventory,
				Output:    os.Stdout,
			}

			orchestrator := &deploy.Orchestrator{
				Deployer:      deployer,
				Inventory:     inventory,
				Output:        os.Stdout,
				Concurrency:   concurrency,
				PrepullImages: prepull,
			}

			// Parse tags
			var tagList []string
			if tags != "" {
				tagList = strings.Split(tags, ",")
				for i, t := range tagList {
					tagList[i] = strings.TrimSpace(t)
				}
			}

			return orchestrator.Deploy(cmd.Context(), tagList)
		},
	}

	cmd.Flags().StringVarP(&inventory, "inventory", "i", "", "Path to Ansible inventory file (required)")
	cmd.Flags().StringVarP(&tags, "tags", "t", "", "Comma-separated list of component tags to deploy")
	cmd.Flags().IntVar(&concurrency, "concurrency", 0, "Max concurrent deployments per wave (0 = unlimited)")
	cmd.Flags().BoolVar(&prepull, "prepull", false, "Pre-pull all container images after foundation wave")

	return cmd
}
