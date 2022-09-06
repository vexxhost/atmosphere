package image_repositories

import "fmt"

func NewSyncWorkflow(project string) *GithubWorkflow {
	return &GithubWorkflow{
		Name: "sync",
		Concurrency: GithubWorkflowConcurrency{
			Group:            "sync",
			CancelInProgress: true,
		},
		On: GithubWorkflowTrigger{
			WorkflowDispatch: GithubWorkflowDispatch{
				Inputs: map[string]GithubWorkflowDispatchInput{
					"ref": {
						Description: "Atmosphere branch, tag or SHA to checkout",
						Required:    true,
						Default:     "main",
					},
				},
			},
			Schedule: []GithubWorkflowSchedule{
				{
					Cron: "0 0 * * *",
				},
			},
		},
		Jobs: map[string]GithubWorkflowJob{
			"image": {
				RunsOn: "ubuntu-latest",
				Steps: []GithubWorkflowStep{
					{
						Name: "Checkout Atmosphere",
						Uses: "actions/checkout@v3",
						With: map[string]string{
							"repository": "vexxhost/atmosphere",
							"ref":        "${{ inputs.ref || 'main' }}",
						},
					},
					{
						Name: "Setup Go",
						Uses: "actions/setup-go@v3",
						With: map[string]string{
							"go-version-file": "go.mod",
							"cache":           "true",
						},
					},
					{
						Name: "Synchronize Image Repository",
						Run:  fmt.Sprintf("go run ./cmd/atmosphere-ci image repo sync %s", project),
						Environment: map[string]string{
							"GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}",
						},
					},
				},
			},
		},
	}
}
