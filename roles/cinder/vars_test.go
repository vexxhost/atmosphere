package cinder

import (
	_ "embed"
	"os"
	"strings"
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
	openstack_helm.HelmValues `yaml:"__cinder_helm_values"`
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
		"cinder_scheduler": "high-priority",
		"cinder_tests": "high-priority",
		"cinder_volume": "high-priority",
		"cinder_volume_usage_audit": "high-priority",
		"cinder_db_purge": "high-priority",
		"cinder_api": "high-priority",
		"cinder_backup": "high-priority",
		"db_sync": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"cinder_scheduler": "kata-clh",
		"cinder_tests": "kata-clh",
		"cinder_volume": "kata-clh",
		"cinder_volume_usage_audit": "kata-clh",
		"cinder_db_purge": "kata-clh",
		"cinder_api": "kata-clh",
		"cinder_backup": "kata-clh",
		"db_sync": "kata-clh",
	}
	vals, err := openstack_helm.CoalescedHelmValues("../../charts/cinder", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Cinder.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}

func TestCinderIdentityAuthOverrides(t *testing.T) {
	var raw struct {
		EndpointValues struct {
			Identity struct {
				Auth map[string]map[string]string `yaml:"auth"`
			} `yaml:"identity"`
		} `yaml:"_cinder_endpoint_values"`
	}

	err := yaml.UnmarshalWithOptions(varsFile, &raw)
	require.NoError(t, err)

	auth := raw.EndpointValues.Identity.Auth
	for _, user := range []string{"admin", "cinder", "nova", "swift", "service", "test"} {
		require.Contains(t, auth, user)
		require.Contains(t, auth[user], "region_name")
		require.Contains(t, auth[user], "username")
		require.Contains(t, auth[user], "password")
		require.Contains(t, auth[user], "project_name")
		require.Contains(t, auth[user], "user_domain_name")
		require.Contains(t, auth[user], "project_domain_name")
	}
	require.NotContains(t, auth, "glance")
}

func TestCinderIdentityEndpointOverrideIsNotRecursive(t *testing.T) {
	var raw map[string]any

	err := yaml.UnmarshalWithOptions(varsFile, &raw)
	require.NoError(t, err)

	helmValues, ok := raw["__cinder_helm_values"].(map[string]any)
	require.True(t, ok)

	endpointsExpr, ok := helmValues["endpoints"].(string)
	require.True(t, ok)
	require.Contains(t, endpointsExpr, "_cinder_identity_endpoint_values")
	require.False(t, strings.Contains(endpointsExpr, "recursive=True"))
}
