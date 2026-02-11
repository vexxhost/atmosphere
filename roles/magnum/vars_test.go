package magnum

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
	openstack_helm.HelmValues `yaml:"_magnum_helm_values"`
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
		"magnum_api": "high-priority",
		"magnum_conductor": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"bootstrap": "kata-clh",
		"db_sync": "kata-clh",
		"magnum_api": "kata-clh",
		"magnum_conductor": "kata-clh",
	}
	vals, err := openstack_helm.CoalescedHelmValues("../../charts/magnum", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Magnum.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}
