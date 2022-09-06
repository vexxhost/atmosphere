package image_repositories

import (
	_ "embed"
	"io"
	"text/template"

	"github.com/go-git/go-billy/v5"
)

//go:embed template/Dockerfile
var dockerfileTemplate string

type Dockerfile struct {
	BindepImage     string
	BindepImageTag  string
	BuilderImage    string
	BuilderImageTag string
	RuntimeImage    string
	RuntimeImageTag string

	template *template.Template
}

func NewDockerfile() (*Dockerfile, error) {
	tmpl, err := template.New("Dockerfile").Parse(dockerfileTemplate)
	if err != nil {
		return nil, err
	}

	return &Dockerfile{
		BindepImage:     "quay.io/vexxhost/bindep-loci",
		BindepImageTag:  "latest",
		BuilderImage:    "quay.io/vexxhost/openstack-builder-focal",
		BuilderImageTag: "latest",
		RuntimeImage:    "quay.io/vexxhost/openstack-runtime-focal",
		RuntimeImageTag: "latest",

		template: tmpl,
	}, nil
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
