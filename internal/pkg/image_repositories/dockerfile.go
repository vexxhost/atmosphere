package image_repositories

import (
	"context"
	_ "embed"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"text/template"

	"github.com/go-git/go-billy/v5"
	"github.com/google/go-github/v47/github"
)

//go:embed template/Dockerfile
var dockerfileTemplate string

type Dockerfile struct {
	Project string

	BindepImage     string
	BindepImageTag  string
	BuilderImage    string
	BuilderImageTag string
	RuntimeImage    string
	RuntimeImageTag string

	template *template.Template
}

func NewDockerfile(ctx context.Context, ir *ImageRepository) (*Dockerfile, error) {
	tmpl, err := template.New("Dockerfile").Parse(dockerfileTemplate)
	if err != nil {
		return nil, err
	}

	builderImageTag, err := getImageTag(ctx, ir.githubClient, "docker-openstack-builder", "openstack-builder-focal")
	if err != nil {
		return nil, err
	}

	runtimeImageTag, err := getImageTag(ctx, ir.githubClient, "docker-openstack-runtime", "openstack-runtime-focal")
	if err != nil {
		return nil, err
	}

	return &Dockerfile{
		Project: ir.Project,

		BindepImage:     "quay.io/vexxhost/bindep-loci",
		BindepImageTag:  "latest",
		BuilderImage:    "quay.io/vexxhost/openstack-builder-focal",
		BuilderImageTag: builderImageTag,
		RuntimeImage:    "quay.io/vexxhost/openstack-runtime-focal",
		RuntimeImageTag: runtimeImageTag,

		template: tmpl,
	}, nil
}

type quayTagList struct {
	Tags          []quayTag `json:"tags"`
	Page          int       `json:"page"`
	HasAdditional bool      `json:"has_additional"`
}

type quayTag struct {
	Name           string `json:"name"`
	Reversion      bool   `json:"reversion"`
	StartTimestamp int32  `json:"start_ts"`
	ManifestDigest string `json:"manifest_digest"`
	IsManifestList bool   `json:"is_manifest_list"`
	Size           int    `json:"size"`
	LastModified   string `json:"last_modified"`
}

func getImageTag(ctx context.Context, client *github.Client, repository string, image string) (string, error) {
	// Grab the latest SHA from the main branch
	commit, _, err := client.Repositories.GetCommitSHA1(ctx, "vexxhost", repository, "main", "")
	if err != nil {
		return "", err
	}

	// Check if the image exists in Quay.io
	url := fmt.Sprintf("https://quay.io/api/v1/repository/vexxhost/%s/tag/?specificTag=%s", image, commit)
	resp, err := http.Get(url)
	if err != nil {
		return "", err
	}

	// Decode the response
	var quayResponse quayTagList
	decoder := json.NewDecoder(resp.Body)
	decoder.DisallowUnknownFields()
	err = decoder.Decode(&quayResponse)
	if err != nil {
		return "", err
	}

	// Check if the tag exists
	if len(quayResponse.Tags) == 0 {
		return "", fmt.Errorf("tag %s does not exist in quay.io/vexxhost/%s", commit, image)
	}

	return commit, nil
}

func (d *Dockerfile) Write(wr io.Writer) error {
	return d.template.Execute(wr, d)
}

func (d *Dockerfile) WriteFile(fs billy.Filesystem) error {
	f, err := fs.Create("Dockerfile")
	if err != nil {
		return err
	}
	defer f.Close()

	return d.Write(f)
}
