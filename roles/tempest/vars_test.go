package tempest

import (
	_ "embed"
	"os"
	"strings"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/require"
)

var (
	//go:embed vars/main.yml
	varsFile []byte
	vars     Vars
)

type Vars struct {
	NetworkBackendSettings struct {
		Ovn struct {
			Conf struct {
				Script    string   `yaml:"script"`
				Whitelist []string `yaml:"whitelist"`
				Tempest   struct {
					Fwaas struct {
						Driver string `yaml:"driver"`
					} `yaml:"fwaas"`
					NetworkFeatureEnabled struct {
						APIExtensions []string `yaml:"api_extensions"`
					} `yaml:"network-feature-enabled"`
				} `yaml:"tempest"`
			} `yaml:"conf"`
		} `yaml:"ovn"`
	} `yaml:"_tempest_network_backend_settings"`
}

func TestMain(m *testing.M) {
	t := &testing.T{}
	err := yaml.UnmarshalWithOptions(varsFile, &vars)
	require.NoError(t, err)

	code := m.Run()
	os.Exit(code)
}

func TestOvnIncludesFwaasApiTests(t *testing.T) {
	ovnVars := vars.NetworkBackendSettings.Ovn.Conf

	require.Equal(t, "ovn", ovnVars.Tempest.Fwaas.Driver)
	require.Contains(t, ovnVars.Tempest.NetworkFeatureEnabled.APIExtensions, "fwaas_v2")
	require.Contains(t, ovnVars.Whitelist, "smoke")
	require.Contains(
		t,
		ovnVars.Whitelist,
		"^neutron_tempest_plugin\\.fwaas\\.api\\.test_fwaasv2_extensions.*",
	)
	require.True(
		t,
		strings.Contains(
			ovnVars.Script,
			"--whitelist-file /etc/tempest/test-whitelist",
		),
	)
}
