package main

import (
	"context"
	"strconv"
	"strings"

	"github.com/google/go-github/v47/github"
	"github.com/gophercloud/gophercloud"
	"github.com/gophercloud/gophercloud/openstack"
	"github.com/gophercloud/gophercloud/openstack/orchestration/v1/stacks"
	"github.com/gophercloud/gophercloud/pagination"
	"github.com/gophercloud/utils/openstack/clientconfig"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

var (
	moleculeCleanupCmd = &cobra.Command{
		Use:   "cleanup",
		Short: "Clean-up stale Heat stacks",

		Run: func(cmd *cobra.Command, args []string) {
			opts, err := clientconfig.AuthOptions(nil)
			if err != nil {
				log.Panic(err)
			}

			provider, err := openstack.AuthenticatedClient(*opts)
			if err != nil {
				log.Panic(err)
			}

			client, err := openstack.NewOrchestrationV1(provider, gophercloud.EndpointOpts{})
			if err != nil {
				log.Panic(err)
			}

			stacks.List(client, stacks.ListOpts{}).EachPage(func(page pagination.Page) (bool, error) {
				allStacks, err := stacks.ExtractStacks(page)
				if err != nil {
					return false, err
				}

				for _, stack := range allStacks {
					if stack.Status == "DELETE_IN_PROGRESS" {
						log.WithFields(log.Fields{
							"stack": stack.Name,
						}).Info("Stack is already being deleted")

						continue
					}

					if !strings.HasPrefix(stack.Name, "atmosphere-") {
						log.Panic("stack name does not start with atmosphere: " + stack.Name)
					}

					s := strings.Split(stack.Name, "-")
					if len(s) != 3 {
						log.Panic("stack name does not have 3 parts: " + stack.Name)
					}

					runId, err := strconv.ParseInt(s[1], 10, 64)
					if err != nil {
						log.Panic(err)
					}
					runAttempt, err := strconv.ParseInt(s[2], 10, 0)
					if err != nil {
						log.Panic(err)
					}

					githubClient := github.NewClient(nil)
					run, _, err := githubClient.Actions.GetWorkflowRunAttempt(context.TODO(), "vexxhost", "atmosphere", runId, int(runAttempt), nil)
					if err != nil {
						log.Panic(err)
					}

					if run.GetStatus() == "completed" {
						log.WithFields(log.Fields{
							"stack": stack.Name,
						}).Info("Deleting stack")

						_ = stacks.Delete(client, stack.Name, stack.ID)
						if err != nil {
							log.Panic(err)
						}
					}
				}

				return true, nil
			})
		},
	}
)

func init() {
	moleculeCmd.AddCommand(moleculeCleanupCmd)
}
