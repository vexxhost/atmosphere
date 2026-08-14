package defaults

import (
	"bytes"
	_ "embed"
	"strings"

	"github.com/goccy/go-yaml"
)

var (
	//go:embed vars/main.yml
	varsFile []byte

	//go:embed defaults/main.yml
	defaultsFile []byte
)

// Define a global variable for the release value.
var release = "main"

func getKubernetesVersion() (string, error) {
	path, err := yaml.PathString("$.atmosphere_kubernetes_version")
	if err != nil {
		return "", err
	}

	var version string
	if err := path.Read(bytes.NewReader(defaultsFile), &version); err != nil {
		return "", err
	}

	return version, nil
}

func GetImages() (map[string]string, error) {
	// Replace {{ release }} with the actual release value
	modifiedVarsFile := []byte(strings.ReplaceAll(string(varsFile), "{{ atmosphere_release }}", release))

	// Fix prefixes for images to allow tests to run
	modifiedVarsFile = []byte(strings.ReplaceAll(string(modifiedVarsFile), "{{ atmosphere_image_prefix }}", ""))

	// Replace {{ atmosphere_kubernetes_version }} with the actual Kubernetes version
	kubernetesVersion, err := getKubernetesVersion()
	if err != nil {
		return nil, err
	}
	modifiedVarsFile = []byte(strings.ReplaceAll(string(modifiedVarsFile), "{{ atmosphere_kubernetes_version }}", kubernetesVersion))

	path, err := yaml.PathString("$._atmosphere_images")
	if err != nil {
		return nil, err
	}

	var images map[string]string
	if err := path.Read(bytes.NewReader(modifiedVarsFile), &images); err != nil {
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
