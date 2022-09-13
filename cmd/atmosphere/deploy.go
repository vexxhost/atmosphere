package main

import (
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"github.com/vexxhost/atmosphere/internal/pkg/deployment"
)

var (
	configFile string
	validate   bool

	deployCmd = &cobra.Command{
		Use: "deploy",
		PreRun: func(cmd *cobra.Command, args []string) {
			// TODO: required config file?
			if configFile != "" {
				// Use config file from the flag.
				viper.SetConfigFile(configFile)
			} else {
				viper.SetConfigName("config")
				viper.AddConfigPath("/etc/atmosphere")
			}

			viper.AutomaticEnv()

			if err := viper.ReadInConfig(); err == nil {
				log.WithFields(log.Fields{
					"config": viper.ConfigFileUsed(),
				}).Info("🕵️  Detected configuration file")
			}
		},
		Run: func(cmd *cobra.Command, args []string) {
			deployment, err := deployment.NewDeployment()
			if err != nil {
				log.WithError(err).Fatal("💥 Failed to initialize")
			}

			err = deployment.Execute()
			if err != nil {
				log.WithError(err).Fatal("💥 Failed to deploy")
			}

			if validate {
				log.Info("🔑 Starting validation")
				if err := deployment.Validate(); err != nil {
					log.WithError(err).Fatal("💥 Failed to validate")
				}
			}

			log.Info("🎉 Successfully deployed")
		},
	}
)

func init() {
	deployCmd.PersistentFlags().StringVar(&configFile, "config", "/etc/atmosphere/config.toml", "Configuration file")
	deployCmd.PersistentFlags().BoolVar(&validate, "validate", false, "Validate post-deployment")

	rootCmd.AddCommand(deployCmd)
}
