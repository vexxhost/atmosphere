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

func TestBaremetalConsoleSafeDefaults(t *testing.T) {
	require.Contains(t, string(defaultsFile),
		`ironic_vnc_namespace: "{{ ironic_helm_release_namespace }}-ironic-vnc"`)
	require.Contains(t, string(defaultsFile),
		"ironic_vnc_network_policy_enabled: true")
	require.Contains(t, string(defaultsFile), "ironic_vnc_disable_mode: fail")
	require.Contains(t, string(varsFile),
		`namespace: "{{ ironic_vnc_namespace if ironic_vnc_enabled | bool else omit }}"`)
	require.Contains(t, string(varsFile), "network_policy_console: >-")
	require.Contains(t, string(tasksFile), "Create bare metal console namespace")
	require.Contains(t, string(tasksFile), "Remove disabled noVNC Ingress")
}
