package main

import (
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/vexxhost/atmosphere/internal/pkg/deployment"
)

var (
	validateDiff bool

	validateCmd = &cobra.Command{
		Use: "validate",
		Run: func(cmd *cobra.Command, args []string) {
			deployment, err := deployment.NewDeployment()
			if err != nil {
				log.WithError(err).Fatal("💥 Failed to initialize")
			}

			err = deployment.Validate(validateDiff)
			if err != nil {
				log.WithError(err).Fatal("💥 Failed to validate")
			}
		},
	}
)

func init() {
	validateCmd.PersistentFlags().BoolVar(&validateDiff, "diff", false, "Print diff between current and desired state")

	rootCmd.AddCommand(validateCmd)
}
