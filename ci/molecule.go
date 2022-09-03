package main

import (
	"context"
	"fmt"
	"strconv"
	"strings"

	"github.com/google/go-github/v47/github"
	"github.com/gophercloud/gophercloud"
	"github.com/gophercloud/gophercloud/openstack"
	"github.com/gophercloud/gophercloud/openstack/orchestration/v1/stacks"
	"github.com/gophercloud/gophercloud/pagination"
	"github.com/gophercloud/utils/openstack/clientconfig"
)

func main() {
	opts, err := clientconfig.AuthOptions(nil)
	if err != nil {
		panic(err)
	}

	provider, err := openstack.AuthenticatedClient(*opts)
	if err != nil {
		panic(err)
	}

	client, err := openstack.NewOrchestrationV1(provider, gophercloud.EndpointOpts{})
	if err != nil {
		panic(err)
	}

	stacks.List(client, stacks.ListOpts{}).EachPage(func(page pagination.Page) (bool, error) {
		allStacks, err := stacks.ExtractStacks(page)
		if err != nil {
			return false, err
		}

		for _, stack := range allStacks {
			if stack.Status == "DELETE_IN_PROGRESS" {
				fmt.Println("skip delete in progress stack: " + stack.Name)
				continue
			}

			if !strings.HasPrefix(stack.Name, "atmosphere-") {
				panic("stack name does not start with atmosphere: " + stack.Name)
			}

			s := strings.Split(stack.Name, "-")
			if len(s) != 3 {
				panic("stack name does not have 3 parts: " + stack.Name)
			}

			runId, err := strconv.ParseInt(s[1], 10, 64)
			if err != nil {
				panic(err)
			}
			runAttempt, err := strconv.ParseInt(s[2], 10, 0)
			if err != nil {
				panic(err)
			}

			githubClient := github.NewClient(nil)
			run, _, err := githubClient.Actions.GetWorkflowRunAttempt(context.TODO(), "vexxhost", "atmosphere", runId, int(runAttempt), nil)
			if err != nil {
				panic(err)
			}

			if run.GetStatus() == "completed" {
				fmt.Println("Deleting stack: " + stack.Name)

				_ = stacks.Delete(client, stack.Name, stack.ID)
				if err != nil {
					panic(err)
				}
			}
		}

		return true, nil
	})
}
