package main

import (
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/vexxhost/atmosphere/internal/pkg/deployment"
)

var (
	validateCmd = &cobra.Command{
		Use: "validate",
		Run: func(cmd *cobra.Command, args []string) {
			deployment, err := deployment.NewDeployment()
			if err != nil {
				log.WithError(err).Fatal("💥 Failed to initialize")
			}

			err = deployment.Validate()
			if err != nil {
				log.WithError(err).Fatal("💥 Failed to validate")
			}
		},
	}
)

func init() {
	rootCmd.AddCommand(validateCmd)
}
