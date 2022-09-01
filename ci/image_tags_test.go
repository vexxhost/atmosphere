package linters

import (
	"os"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"gopkg.in/yaml.v3"
)

func TestPrometheusEthtoolExporterTag(t *testing.T) {
	imageFile, err := os.ReadFile("../images/prometheus-ethtool-exporter/ref")
	assert.NoError(t, err)

	imageTag := strings.TrimSpace(string(imageFile))

	data, err := os.ReadFile("../roles/prometheus_ethtool_exporter/defaults/main.yml")
	assert.NoError(t, err)

	defaults := make(map[interface{}]interface{})
	err = yaml.Unmarshal(data, &defaults)
	assert.NoError(t, err)

	ansibleTag, ok := defaults["prometheus_ethtool_exporter_image_tag"]
	if assert.True(t, ok) {
		assert.Equal(t, imageTag, ansibleTag)
	}
}
