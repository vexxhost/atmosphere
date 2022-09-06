package image_repositories

import (
	"io"

	"github.com/go-git/go-billy/v5"
	"github.com/goccy/go-yaml"
)

type DependabotConfig struct {
	Version int                `yaml:"version"`
	Updates []DependabotUpdate `yaml:"updates"`
}

type DependabotUpdate struct {
	PackageEcosystem string             `yaml:"package-ecosystem"`
	Directory        string             `yaml:"directory"`
	Schedule         DependabotSchedule `yaml:"schedule"`
}

type DependabotSchedule struct {
	Interval string `yaml:"interval"`
}

func NewDependabotConfig() *DependabotConfig {
	return &DependabotConfig{
		Version: 2,
		Updates: []DependabotUpdate{},
	}
}

func (d *DependabotConfig) Write(wr io.Writer) error {
	bytes, err := yaml.Marshal(d)
	if err != nil {
		return err
	}

	_, err = wr.Write(bytes)
	return err
}

func (d *DependabotConfig) WriteFile(fs billy.Filesystem) error {
	f, err := fs.Create(".github/dependabot.yml")
	if err != nil {
		return err
	}
	defer f.Close()

	return d.Write(f)
}
