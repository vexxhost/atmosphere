package image_repositories

import (
	"fmt"
	"io"

	"github.com/go-git/go-billy/v5"
	"github.com/goccy/go-yaml"
)

type GithubWorkflow struct {
	Name        string                       `yaml:"name"`
	Concurrency GithubWorkflowConcurrency    `yaml:"concurrency"`
	On          GithubWorkflowTrigger        `yaml:"on"`
	Jobs        map[string]GithubWorkflowJob `yaml:"jobs"`
}

type GithubWorkflowTrigger struct {
	PullRequest      GithubWorkflowPullRequest `yaml:"pull_request,omitempty"`
	Push             GithubWorkflowPush        `yaml:"push,omitempty"`
	Schedule         []GithubWorkflowSchedule  `yaml:"schedule,omitempty"`
	WorkflowDispatch GithubWorkflowDispatch    `yaml:"workflow_dispatch,omitempty"`
}

type GithubWorkflowPullRequest struct {
	Types []string `yaml:"types,omitempty"`
}

type GithubWorkflowPush struct {
	Branches []string `yaml:"branches"`
}

type GithubWorkflowSchedule struct {
	Cron string `yaml:"cron"`
}

type GithubWorkflowDispatch struct {
	Inputs map[string]GithubWorkflowDispatchInput `yaml:"inputs,omitempty"`
}

type GithubWorkflowDispatchInput struct {
	Description string `yaml:"description"`
	Required    bool   `yaml:"required"`
	Default     string `yaml:"default"`
}

type GithubWorkflowConcurrency struct {
	Group            string `yaml:"group"`
	CancelInProgress bool   `yaml:"cancel-in-progress"`
}

type GithubWorkflowJob struct {
	Permissions map[string]string `yaml:"permissions,omitempty"`
	RunsOn      string                 `yaml:"runs-on"`
	Strategy    GithubWorkflowStrategy `yaml:"strategy,omitempty"`
	Steps       []GithubWorkflowStep   `yaml:"steps"`
}

func (j GithubWorkflowJob) DeepCopy() GithubWorkflowJob {
	job := GithubWorkflowJob{}
	job.RunsOn = j.RunsOn
	job.Strategy = j.Strategy.DeepCopy()

	job.Steps = make([]GithubWorkflowStep, len(j.Steps))
	for i, step := range j.Steps {
		job.Steps[i] = step.DeepCopy()
	}

	return job
}

type GithubWorkflowStrategy struct {
	Matrix map[string]interface{} `yaml:"matrix"`
}

func (s *GithubWorkflowStrategy) DeepCopy() GithubWorkflowStrategy {
	strategy := *s
	strategy.Matrix = make(map[string]interface{})
	for k, v := range s.Matrix {
		strategy.Matrix[k] = v
	}

	return strategy
}

type GithubWorkflowStep struct {
	Name        string            `yaml:"name"`
	Run         string            `yaml:"run,omitempty"`
	Uses        string            `yaml:"uses,omitempty"`
	If          string            `yaml:"if,omitempty"`
	With        map[string]string `yaml:"with,omitempty"`
	Environment map[string]string `yaml:"env,omitempty"`
}

func (s *GithubWorkflowStep) DeepCopy() GithubWorkflowStep {
	step := *s
	step.With = make(map[string]string)
	for k, v := range s.With {
		step.With[k] = v
	}

	step.Environment = make(map[string]string)
	for k, v := range s.Environment {
		step.Environment[k] = v
	}

	return step
}

func (g *GithubWorkflow) Write(wr io.Writer) error {
	bytes, err := yaml.Marshal(g)
	if err != nil {
		return err
	}

	_, err = wr.Write(bytes)
	return err
}

func (g *GithubWorkflow) WriteFile(fs billy.Filesystem) error {
	file := fmt.Sprintf(".github/workflows/%s.yml", g.Name)

	f, err := fs.Create(file)
	if err != nil {
		return err
	}
	defer f.Close()

	return g.Write(f)
}
