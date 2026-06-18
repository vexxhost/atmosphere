package nova

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
)

type Vars struct {
	openstack_helm.HelmValues `yaml:"_nova_helm_values"`
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
		"bootstrap": "high-priority",
		"db_sync": "high-priority",
		"nova_archive_deleted_rows": "high-priority",
		"nova_cell_setup": "high-priority",
		"nova_service_cleaner": "high-priority",
		"nova_compute": "high-priority",
		"nova_api_metadata": "high-priority",
		"nova_api_osapi": "high-priority",
		"nova_conductor": "high-priority",
		"nova_novncproxy": "high-priority",
		"nova_scheduler": "high-priority",
		"nova_spiceproxy": "high-priority",
		"nova_tests": "high-priority",
		"nova_compute_ironic": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"bootstrap": "kata-clh",
		"db_sync": "kata-clh",
		"nova_archive_deleted_rows": "kata-clh",
		"nova_cell_setup": "kata-clh",
		"nova_service_cleaner": "kata-clh",
		"nova_compute": "kata-clh",
		"nova_api_metadata": "kata-clh",
		"nova_api_osapi": "kata-clh",
		"nova_conductor": "kata-clh",
		"nova_novncproxy": "kata-clh",
		"nova_scheduler": "kata-clh",
		"nova_spiceproxy": "kata-clh",
		"nova_tests": "kata-clh",
		"nova_compute_ironic": "kata-clh",
	}
	vals, err := openstack_helm.CoalescedHelmValues("../../charts/nova", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Nova.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}
