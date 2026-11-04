package glance

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
	//go:embed vars/main.yml
	varsFile []byte
	vars     Vars

	//go:embed tasks/main.yml
	tasksFile []byte
)

type Vars struct {
	openstack_helm.HelmValues `yaml:"_glance_helm_values"`
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
		"db_sync":      "high-priority",
		"glance_api":   "high-priority",
		"glance_tests": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"db_sync":      "kata-clh",
		"glance_api":   "kata-clh",
		"glance_tests": "kata-clh",
	}
	vals, err := openstack_helm.CoalescedHelmValues("../../charts/glance", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Glance.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}

func TestImageConfigurationIsForwarded(t *testing.T) {
	for _, expected := range []string{
		`glance_image_oci_reference: "{{ item.oci_reference | default('') }}"`,
		`glance_image_oci_path: "{{ item.oci_path | default('') }}"`,
		`glance_image_oci_sha512: "{{ item.oci_sha512 | default('') }}"`,
		`glance_image_oci_architecture: "{{ item.oci_architecture | default('amd64') }}"`,
		`glance_image_oci_authfile: "{{ item.oci_authfile | default('') }}"`,
		`glance_image_owner: "{{ item.owner | default(omit) }}"`,
		`glance_image_owner_domain: "{{ item.owner_domain | default(omit) }}"`,
	} {
		require.Contains(t, string(tasksFile), expected)
	}
}
