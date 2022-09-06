package main

import (
	"context"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/vexxhost/atmosphere/internal/pkg/image_repositories"
)

var (
	imageRepoSyncCmd = &cobra.Command{
		Use:   "sync [project]",
		Short: "Sync image repository",
		Args:  cobra.MinimumNArgs(1),

		Run: func(cmd *cobra.Command, args []string) {
			ctx := context.TODO()

			repo := image_repositories.NewImageRepository(args[0])
			err := repo.Synchronize(ctx)
			if err != nil {
				log.Panic(err)
			}
		},
	}
)

func init() {
	imageRepoCmd.AddCommand(imageRepoSyncCmd)
}
