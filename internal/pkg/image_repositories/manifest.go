package image_repositories

import (
	"context"
	"fmt"
	"io"

	"github.com/go-git/go-billy/v5"
	"github.com/goccy/go-yaml"
	"github.com/google/go-github/v57/github"
)

type ReleaseManifest struct {
	SHA string `json:"sha"`
}

type ImageManifest struct {
	Wallaby  *ReleaseManifest `yaml:"wallaby"`
	Xena     *ReleaseManifest `yaml:"xena"`
	Yoga     *ReleaseManifest `yaml:"yoga"`
	Zed      *ReleaseManifest `yaml:"zed"`
	Antelope *ReleaseManifest `yaml:"2023.1"`
	Bobcat   *ReleaseManifest `yaml:"2023.2"`
}

func NewImageManifest(project string, client *github.Client) (*ImageManifest, error) {
	wallaby, err := getReleaseManifest(client, project, "wallaby")
	if err != nil {
		return nil, err
	}

	xena, err := getReleaseManifest(client, project, "xena")
	if err != nil {
		return nil, err
	}

	yoga, err := getReleaseManifest(client, project, "yoga")
	if err != nil {
		return nil, err
	}

	zed, err := getReleaseManifest(client, project, "zed")
	if err != nil {
		return nil, err
	}

	antelope, err := getReleaseManifest(client, project, "2023.1")
	if err != nil {
		return nil, err
	}

	bobcat, err := getReleaseManifest(client, project, "2023.2")
	if err != nil {
		return nil, err
	}

	return &ImageManifest{
		Wallaby:  wallaby,
		Xena:     xena,
		Yoga:     yoga,
		Zed:      zed,
		Antelope: antelope,
		Bobcat:   bobcat,
	}, nil
}

func (m *ImageManifest) Write(wr io.Writer) error {
	bytes, err := yaml.Marshal(m)
	if err != nil {
		return err
	}

	_, err = wr.Write(bytes)
	return err
}

func (m *ImageManifest) WriteFile(fs billy.Filesystem) error {
	f, err := fs.Create("manifest.yml")
	if err != nil {
		return err
	}
	defer f.Close()

	return m.Write(f)
}

func getReleaseManifest(client *github.Client, project, release string) (*ReleaseManifest, error) {
	branchName := fmt.Sprintf("stable/%s", release)

	gitOrg := "openstack"
	if _, ok := FORKED_PROJECTS[project]; ok {
		gitOrg = "vexxhost"
	}

	branch, _, err := client.Repositories.GetBranch(context.TODO(), gitOrg, project, branchName, 2)
	if err != nil {
		return nil, err
	}

	return &ReleaseManifest{
		SHA: branch.GetCommit().GetSHA(),
	}, nil
}
