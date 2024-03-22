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

func GetImages() (map[string]string, error) {
	path, err := yaml.PathString("$._atmosphere_images")
	if err != nil {
		return nil, err
	}

	var images map[string]string
	if err := path.Read(bytes.NewReader(varsFile), &images); err != nil {
		return nil, err
	}

	return images, nil
}

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
