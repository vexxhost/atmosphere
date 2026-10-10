package openstack_helm_endpoints

import (
	_ "embed"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/require"
)

var (
	//go:embed defaults/main.yml
	defaultsFile []byte
)

type Defaults struct {
	IronicNoVNCHost string `yaml:"openstack_helm_endpoints_ironic_novnc_host"`
}

func TestIronicNoVNCHostDefaultsToDistinctName(t *testing.T) {
	var defaults Defaults
	err := yaml.UnmarshalWithOptions(defaultsFile, &defaults)
	require.NoError(t, err)

	require.Contains(t, defaults.IronicNoVNCHost, "regex_replace")
	require.Contains(t, defaults.IronicNoVNCHost, "baremetal-console")
	require.NotContains(t, defaults.IronicNoVNCHost, "# ]]]")
}
