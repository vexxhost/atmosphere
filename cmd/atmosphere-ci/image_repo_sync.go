package main

import (
	"context"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/vexxhost/atmosphere/internal/pkg/image_repositories"
)

var (
	admin bool

	imageRepoSyncCmd = &cobra.Command{
		Use:   "sync [project]",
		Short: "Sync image repository",
		Args:  cobra.MinimumNArgs(1),

		Run: func(cmd *cobra.Command, args []string) {
			ctx := context.TODO()

			repo := image_repositories.NewImageRepository(args[0])

			if admin {
				repo.UpdateGithubConfiguration(ctx)
			}

			err := repo.Synchronize(ctx)
			if err != nil {
				log.Panic(err)
			}
		},
	}
)

func init() {
	imageRepoCmd.PersistentFlags().BoolVar(&admin, "admin", false, "Run using admin PAT (will update repo configs)")

	imageRepoCmd.AddCommand(imageRepoSyncCmd)
}
