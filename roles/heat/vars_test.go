package heat

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
	openstack_helm.HelmValues `yaml:"_heat_helm_values"`
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
		"db_sync": "high-priority",
		"heat_api": "high-priority",
		"heat_cloudwatch": "high-priority",
		"heat_engine": "high-priority",
		"heat_engine_cleaner": "high-priority",
		"heat_tests": "high-priority",
		"bootstrap": "high-priority",
		"heat_cfn": "high-priority",
		"heat_purge_deleted": "high-priority",
		"heat_trusts": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"db_sync": "kata-clh",
		"heat_api": "kata-clh",
		"heat_cloudwatch": "kata-clh",
		"heat_engine": "kata-clh",
		"heat_engine_cleaner": "kata-clh",
		"heat_tests": "kata-clh",
		"bootstrap": "kata-clh",
		"heat_cfn": "kata-clh",
		"heat_purge_deleted": "kata-clh",
		"heat_trusts": "kata-clh",
	}

	vals, err := openstack_helm.CoalescedHelmValues("../../charts/heat", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Heat.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}
