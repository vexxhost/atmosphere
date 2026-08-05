package ironic

import (
	_ "embed"
	"os"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/require"

	"github.com/vexxhost/atmosphere/internal/openstack_helm"
	"github.com/vexxhost/atmosphere/internal/testutils"
)

var (
	//go:embed defaults/main.yml
	defaultsFile []byte

	//go:embed vars/main.yml
	varsFile []byte
	vars     Vars

	//go:embed tasks/main.yml
	tasksFile []byte
)

type Vars struct {
	openstack_helm.HelmValues `yaml:"_ironic_helm_values"`
}

type Defaults struct {
	BaremetalConsoleAllowInsecureTLS  bool   `yaml:"ironic_vnc_allow_insecure_tls"`
	BaremetalConsoleCASecretName      string `yaml:"ironic_vnc_ca_secret_name"`
	BaremetalConsoleCASecretKey       string `yaml:"ironic_vnc_ca_secret_key"`
	BaremetalConsoleCAMountPath       string `yaml:"ironic_vnc_ca_mount_path"`
	BaremetalConsoleTLSMinimumVersion string `yaml:"ironic_vnc_tls_minimum_version"`
}

func TestMain(m *testing.M) {
	t := &testing.T{}
	err := yaml.UnmarshalWithOptions(varsFile, &vars)
	require.NoError(t, err)

	code := m.Run()
	os.Exit(code)
}

func TestHelmValues(t *testing.T) {
	// (rlin): Before you add any new priority class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_priority_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_priority_class" }}
	vars.HelmValues.Pod.PriorityClass = map[string]string{
		"bootstrap":         "high-priority",
		"db_sync":           "high-priority",
		"ironic_api":        "high-priority",
		"ironic_conductor":  "high-priority",
		"ironic_novncproxy": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"bootstrap":         "kata-clh",
		"db_sync":           "kata-clh",
		"ironic_api":        "kata-clh",
		"ironic_conductor":  "kata-clh",
		"ironic_novncproxy": "kata-clh",
	}
	vals, err := openstack_helm.CoalescedHelmValues("../../charts/ironic", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Ironic.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}

func TestBaremetalConsoleImageUsesAtmosphereCatalog(t *testing.T) {
	require.NotContains(t, string(defaultsFile), "ironic_vnc_image")
	require.Contains(t, string(tasksFile),
		"atmosphere_images.get('ironic_console') is string")
	require.Contains(t, string(varsFile),
		`console_image: "{{ atmosphere_images.get('ironic_console', omit) }}"`)
	require.NotContains(t, string(varsFile), "ironic_vnc_image")
}

func TestBaremetalConsoleTLSContract(t *testing.T) {
	var defaults Defaults
	err := yaml.UnmarshalWithOptions(defaultsFile, &defaults)
	require.NoError(t, err)
	require.False(t, defaults.BaremetalConsoleAllowInsecureTLS)
	require.Empty(t, defaults.BaremetalConsoleCASecretName)
	require.Equal(t, "ca.crt", defaults.BaremetalConsoleCASecretKey)
	require.Equal(t, "/etc/ironic-console-ca", defaults.BaremetalConsoleCAMountPath)
	require.Equal(t, "1.2", defaults.BaremetalConsoleTLSMinimumVersion)

	for _, expected := range []string{
		"'name': 'ALLOW_INSECURE_TLS'",
		"'name': 'BMC_TLS_MINIMUM_VERSION'",
		"'name': 'BMC_TLS_CIPHERS'",
		"'name': 'BMC_CA_FILE'",
		"'secretName': ironic_vnc_ca_secret_name",
		"'key': ironic_vnc_ca_secret_key",
	} {
		require.Contains(t, string(varsFile), expected)
	}

	require.Contains(t, string(tasksFile),
		"ironic_vnc_ca_secret_key in _ironic_vnc_ca_secret.resources.0.data")
}
