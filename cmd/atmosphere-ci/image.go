package main

import (
	"github.com/spf13/cobra"
)

var imageCmd = &cobra.Command{
	Use:   "image",
	Short: "Image sub-commands",
}

func init() {
	rootCmd.AddCommand(imageCmd)
}
