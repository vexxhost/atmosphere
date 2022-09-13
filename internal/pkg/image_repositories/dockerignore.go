package image_repositories

import (
	"io"

	"github.com/go-git/go-billy/v5"
)

type DockerIgnore struct {
}

func NewDockerIgnore() *DockerIgnore {
	return &DockerIgnore{}
}

func (d *DockerIgnore) Write(wr io.Writer) error {
	_, err := wr.Write([]byte("*\n"))
	return err
}

func (d *DockerIgnore) WriteFile(fs billy.Filesystem) error {
	f, err := fs.Create(".dockerignore")
	if err != nil {
		return err
	}
	defer f.Close()

	return d.Write(f)
}
