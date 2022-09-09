package image_repositories

import (
	_ "embed"
	"io"
	"text/template"

	"github.com/go-git/go-billy/v5"
)

//go:embed template/README.md
var readmeTemplate string

type Readme struct {
	Project string

	template *template.Template
}

func NewReadme(project string) (*Readme, error) {
	tmpl, err := template.New("README.md").Parse(readmeTemplate)
	if err != nil {
		return nil, err
	}

	return &Readme{
		Project: project,

		template: tmpl,
	}, nil
}

func (r *Readme) Write(wr io.Writer) error {
	return r.template.Execute(wr, r)
}

func (r *Readme) WriteFile(fs billy.Filesystem) error {
	f, err := fs.Create("README.md")
	if err != nil {
		return err
	}
	defer f.Close()

	return r.Write(f)
}
