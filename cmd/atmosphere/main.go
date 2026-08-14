package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "atmosphere",
		Short: "Atmosphere deployment orchestrator",
		Long:  "Parallel deployment orchestrator for the Atmosphere cloud platform.",
	}

	rootCmd.AddCommand(newDeployCmd())

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
