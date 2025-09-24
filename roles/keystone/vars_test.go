package keystone

import (
	_ "embed"
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
	openstack_helm.HelmValues `yaml:"_keystone_helm_values"`
}

func TestHelmValues(t *testing.T) {
	err := yaml.UnmarshalWithOptions(varsFile, &vars)
	require.NoError(t, err)

	// (rlin): Before you add any new priority class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_priority_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_priority_class" }}
	vars.HelmValues.Pod.PriorityClass = map[string]string{
		"keystone_fernet_rotate": "high-priority",
		"keystone_credential_rotate": "high-priority",
		"keystone_fernet_setup": "high-priority",
		"keystone_tests": "high-priority",
		"keystone_api": "high-priority",
		"bootstrap": "high-priority",
		"keystone_credential_cleanup": "high-priority",
		"keystone_credential_setup": "high-priority",
		"db_init": "high-priority",
		"db_sync": "high-priority",
		"keystone_domain_manage": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"keystone_fernet_rotate": "kata-clh",
		"keystone_credential_rotate": "kata-clh",
		"keystone_fernet_setup": "kata-clh",
		"keystone_tests": "kata-clh",
		"keystone_api": "kata-clh",
		"bootstrap": "kata-clh",
		"keystone_credential_cleanup": "kata-clh",
		"keystone_credential_setup": "kata-clh",
		"db_init": "kata-clh",
		"db_sync": "kata-clh",
		"keystone_domain_manage": "kata-clh",
	}

	vals, err := openstack_helm.CoalescedHelmValues("../../charts/keystone", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Keystone.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}
