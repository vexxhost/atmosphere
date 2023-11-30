package defaults

import (
	"bytes"
	_ "embed"

	"github.com/goccy/go-yaml"
)

var (
	//go:embed vars/main.yml
	varsFile []byte
)

func GetImageByKey(key string) (string, error) {
	path, err := yaml.PathString("$._atmosphere_images." + key)
	if err != nil {
		return "", err
	}

	var image string
	if err := path.Read(bytes.NewReader(varsFile), &image); err != nil {
		return "", err
	}

	return image, nil
}
