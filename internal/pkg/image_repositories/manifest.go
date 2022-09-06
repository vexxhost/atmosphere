package image_repositories

import (
	"fmt"
	"io"

	"code.gitea.io/sdk/gitea"
	"github.com/go-git/go-billy/v5"
	"github.com/goccy/go-yaml"
)

type ReleaseManifest struct {
	SHA string `json:"sha"`
}

type ImageManifest struct {
	Wallaby *ReleaseManifest `yaml:"wallaby"`
	Xena    *ReleaseManifest `yaml:"xena"`
	Yoga    *ReleaseManifest `yaml:"yoga"`
}

func NewImageManifest(project string) (*ImageManifest, error) {
	client, err := gitea.NewClient("https://opendev.org")
	if err != nil {
		return nil, err
	}

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

	return &ImageManifest{
		Wallaby: wallaby,
		Xena:    xena,
		Yoga:    yoga,
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

func getReleaseManifest(client *gitea.Client, project, release string) (*ReleaseManifest, error) {
	branchName := fmt.Sprintf("stable/%s", release)

	branch, _, err := client.GetRepoBranch("openstack", project, branchName)
	if err != nil {
		return nil, err
	}

	return &ReleaseManifest{
		SHA: branch.Commit.ID,
	}, nil
}
