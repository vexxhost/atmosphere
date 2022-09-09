package main

import (
	"github.com/spf13/cobra"
)

var imageRepoCmd = &cobra.Command{
	Use:   "repo",
	Short: "Image repository sub-commands",
}

func init() {
	imageCmd.AddCommand(imageRepoCmd)
}
