package main

import (
	"context"
	"fmt"
	"os"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"github.com/vexxhost/atmosphere/internal/pkg/deployment"
	"github.com/vexxhost/atmosphere/internal/pkg/openstack_helm"
)

var (
	configFile string

	rootCmd = &cobra.Command{
		Use: "atmosphere",
		Run: func(cmd *cobra.Command, args []string) {
			deployment, err := deployment.NewDeployment()
			if err != nil {
				log.WithError(err).Fatal("💥 Failed to initialize")
			}

			err = deployment.Execute()
			if err != nil {
				log.WithError(err).Fatal("💥 Failed to deploy")
			}

			err = openstack_helm.Deploy(context.TODO())
			if err != nil {
				log.WithError(err).Fatal("Failed to deploy OpenStack charts")
			}
		},
	}
)

func main() {
	cobra.OnInitialize(initConfig)
	rootCmd.PersistentFlags().StringVar(&configFile, "config", "/etc/atmosphere/config.toml", "Configuration file")

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func initConfig() {
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
}
