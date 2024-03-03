package cmd

import (
	"context"
	"os"
	"sync"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"github.com/vexxhost/atmosphere/internal/deploy"
)

var (
	dryRun bool

	deployCmd = &cobra.Command{
		Use:   "deploy",
		Short: "Execute a deployment",
		Run: func(cmd *cobra.Command, args []string) {
			if dryRun {
				log.Warn("Running in dry-run mode")
			}

			config, err := kubeconfigArgs.ToRESTConfig()
			if err != nil {
				log.Fatal(err)
			}

			managerSet, err := deploy.NewManagerSet(config, &deploy.ManagerOptions{
				DryRun: dryRun,
			})
			if err != nil {
				log.Fatal(err)
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
