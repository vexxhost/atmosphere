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
)

type Vars struct {
	openstack_helm.HelmValues `yaml:"_ironic_helm_values"`
}

type Defaults struct {
	EnabledBootInterfaces                  string   `yaml:"ironic_enabled_boot_interfaces"`
	RedfishVirtualMediaEnabled             bool     `yaml:"ironic_redfish_virtual_media_enabled"`
	RedfishVirtualMediaUseSwift            bool     `yaml:"ironic_redfish_virtual_media_use_swift"`
	RedfishVirtualMediaBootloaderByArch    string   `yaml:"ironic_redfish_virtual_media_bootloader_by_arch"`
	RedfishVirtualMediaGrubConfigPath      string   `yaml:"ironic_redfish_virtual_media_grub_config_path"`
	RedfishVirtualMediaFileURLAllowedPaths []string `yaml:"ironic_redfish_virtual_media_file_url_allowed_paths"`
}

type IronicVars struct {
	HelmValues struct {
		Conf struct {
			Ironic struct {
				Default struct {
					EnabledBootInterfaces string `yaml:"enabled_boot_interfaces"`
				} `yaml:"DEFAULT"`
			} `yaml:"ironic"`
		} `yaml:"conf"`
	} `yaml:"_ironic_helm_values"`
}

func TestRedfishVirtualMediaDefaults(t *testing.T) {
	var defaults Defaults
	err := yaml.UnmarshalWithOptions(defaultsFile, &defaults)
	require.NoError(t, err)
	require.Equal(t, "ipxe,pxe,redfish-virtual-media", defaults.EnabledBootInterfaces)
	require.False(t, defaults.RedfishVirtualMediaEnabled)
	require.False(t, defaults.RedfishVirtualMediaUseSwift)
	require.Equal(t, "x86_64:file:///usr/share/ironic/esp/x86_64.img", defaults.RedfishVirtualMediaBootloaderByArch)
	require.Equal(t, "EFI/ubuntu/grub.cfg", defaults.RedfishVirtualMediaGrubConfigPath)
	require.Contains(t, defaults.RedfishVirtualMediaFileURLAllowedPaths, "/usr/share/ironic/esp")
}

func TestRedfishVirtualMediaBootInterfaceIsAlwaysAdvertised(t *testing.T) {
	var ironicVars IronicVars
	err := yaml.UnmarshalWithOptions(varsFile, &ironicVars)
	require.NoError(t, err)
	require.Equal(t, "{{ ironic_enabled_boot_interfaces }}", ironicVars.HelmValues.Conf.Ironic.Default.EnabledBootInterfaces)
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
		"bootstrap":        "high-priority",
		"db_sync":          "high-priority",
		"ironic_api":       "high-priority",
		"ironic_conductor": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"bootstrap":        "kata-clh",
		"db_sync":          "kata-clh",
		"ironic_api":       "kata-clh",
		"ironic_conductor": "kata-clh",
	}
	vals, err := openstack_helm.CoalescedHelmValues("../../charts/ironic", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Ironic.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}
