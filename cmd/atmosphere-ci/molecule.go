package main

import (
	"github.com/spf13/cobra"
)

var moleculeCmd = &cobra.Command{
	Use:   "molecule",
	Short: "Molecule sub-commands",
}

func init() {
	rootCmd.AddCommand(moleculeCmd)
}
