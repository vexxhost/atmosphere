package cmd

import (
	"context"
	"os"
	"sync"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	logf "sigs.k8s.io/controller-runtime/pkg/log"

	"github.com/vexxhost/atmosphere/internal/deploy"
)

var (
	dryRun bool

	deployCmd = &cobra.Command{
		Use:   "deploy",
		Short: "Execute a deployment",
		Run: func(cmd *cobra.Command, args []string) {
			logger := logf.Log.WithName("deploy")

			config, err := kubeconfigArgs.ToRESTConfig()
			if err != nil {
				logger.Error(err, "Failed to create Kubernetes client configuration")
				os.Exit(1)
			}

			managerSet, err := deploy.NewManagerSet(config, &deploy.ManagerOptions{
				DryRun: dryRun,
				Logger: logger,
			})
			if err != nil {
				logger.Error(err, "Failed to create manager set")
				os.Exit(1)
			}

			v := viper.New()
			v.Set("image", "docker.io/library/rabbitmq:3.10.2-management")

			var wg sync.WaitGroup
			services := []string{
				"barbican",
				"cinder",
				"glance",
				"heat",
				"keystone",
				"magnum",
				"manila",
				"neutron",
				"nova",
				"octavia",
				"senlin",
			}
			for _, service := range services {
				wg.Add(1)

				go func(service string) {
					defer wg.Done()

					err = managerSet.Rabbitmq.Deploy(context.TODO(), deploy.RabbitmqOptionsFromViper(service, v))
					if err != nil {
						os.Exit(1)
					}
				}(service)
			}
			wg.Wait()
		},
	}
)

func init() {
	deployCmd.Flags().BoolVarP(&dryRun, "dry-run", "d", false, "Dry-run (do not make any changes)")

	rootCmd.AddCommand(deployCmd)
}
