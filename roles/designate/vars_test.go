package designate

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
	openstack_helm.HelmValues `yaml:"_designate_helm_values"`
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
		"designate_api": "high-priority",
		"designate_central": "high-priority",
		"designate_mdns": "high-priority",
		"designate_producer": "high-priority",
		"designate_sink": "high-priority",
		"designate_worker": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"db_sync": "kata-clh",
		"designate_api": "kata-clh",
		"designate_central": "kata-clh",
		"designate_mdns": "kata-clh",
		"designate_producer": "kata-clh",
		"designate_sink": "kata-clh",
		"designate_worker": "kata-clh",
	}
	vals, err := openstack_helm.CoalescedHelmValues("../../charts/designate", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Designate.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}
