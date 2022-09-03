package linters

import (
	"fmt"
	"os"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gopkg.in/yaml.v3"
)

func getImageTag(t *testing.T, file string) string {
	imageFile, err := os.ReadFile(file)
	require.NoError(t, err)

	return strings.TrimSpace(string(imageFile))
}

func getAnsibleTag(t *testing.T, role string) string {
	path := fmt.Sprint("../roles/", role, "/defaults/main.yml")
	data, err := os.ReadFile(path)
	require.NoError(t, err)

	defaults := make(map[interface{}]interface{})
	err = yaml.Unmarshal(data, &defaults)
	require.NoError(t, err)

	key := fmt.Sprint(role, "_image_tag")
	ansibleTag, ok := defaults[key]
	require.True(t, ok)

	return ansibleTag.(string)
}

func assertImageTag(t *testing.T, imageTagFile string, ansibleRole string) {
	imageTag := getImageTag(t, imageTagFile)
	ansibleTag := getAnsibleTag(t, ansibleRole)

	assert.Equal(t, imageTag, ansibleTag)
}

func TestPrometheusEthtoolExporterTag(t *testing.T) {
	assertImageTag(t, "../images/prometheus-ethtool-exporter/ref", "prometheus_ethtool_exporter")
}

func TestOpenstackHelmKeystoneTag(t *testing.T) {
	assertImageTag(t, "../images/openstack/projects/keystone/wallaby/ref", "openstack_helm_keystone")
}
