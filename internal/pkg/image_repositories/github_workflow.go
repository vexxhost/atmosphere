package image_repositories

import (
	"io"

	"github.com/go-git/go-billy/v5"
	"github.com/goccy/go-yaml"
)

type GithubWorkflow struct {
	Name string                       `yaml:"name"`
	On   GithubWorkflowTrigger        `yaml:"on"`
	Jobs map[string]GithubWorkflowJob `yaml:"jobs"`
}

type GithubWorkflowTrigger struct {
	PullRequest GithubWorkflowPullRequest `yaml:"pull_request"`
	Push        GithubWorkflowPush        `yaml:"push"`
}

type GithubWorkflowPullRequest struct {
}

type GithubWorkflowPush struct {
	Branches []string `yaml:"branches"`
}

type GithubWorkflowJob struct {
	RunsOn   string                 `yaml:"runs-on"`
	Strategy GithubWorkflowStrategy `yaml:"strategy"`
	Steps    []GithubWorkflowStep   `yaml:"steps"`
}

type GithubWorkflowStrategy struct {
	Matrix map[string][]string `yaml:"matrix"`
}

type GithubWorkflowStep struct {
	Name string            `yaml:"name"`
	Run  string            `yaml:"run,omitempty"`
	Uses string            `yaml:"uses,omitempty"`
	If   string            `yaml:"if,omitempty"`
	With map[string]string `yaml:"with,omitempty"`
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
	f, err := fs.Create(".github/workflows/build.yml")
	if err != nil {
		return err
	}
	defer f.Close()

	return g.Write(f)
}
