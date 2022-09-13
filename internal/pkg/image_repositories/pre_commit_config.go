package image_repositories

import (
	"io"

	"github.com/go-git/go-billy/v5"
	"github.com/goccy/go-yaml"
)

type PreCommitConfig struct {
	Repositories []PreCommitRepository `yaml:"repos"`
}

type PreCommitRepository struct {
	Repository string          `yaml:"repo"`
	Revision   string          `yaml:"rev"`
	Hooks      []PreCommitHook `yaml:"hooks"`
}

type PreCommitHook struct {
	ID     string   `yaml:"id"`
	Stages []string `yaml:"stages"`
}

func NewPreCommitConfig() *PreCommitConfig {
	return &PreCommitConfig{
		Repositories: []PreCommitRepository{
			{
				Repository: "https://github.com/compilerla/conventional-pre-commit",
				Revision:   "v2.0.0",
				Hooks: []PreCommitHook{
					{
						ID:     "conventional-pre-commit",
						Stages: []string{"commit-msg"},
					},
				},
			},
		},
	}
}

func (c *PreCommitConfig) Write(wr io.Writer) error {
	bytes, err := yaml.Marshal(c)
	if err != nil {
		return err
	}

	_, err = wr.Write(bytes)
	return err
}

func (c *PreCommitConfig) WriteFile(fs billy.Filesystem) error {
	f, err := fs.Create(".pre-commit-config.yaml")
	if err != nil {
		return err
	}
	defer f.Close()

	return c.Write(f)
}
