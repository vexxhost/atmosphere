package neutron

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
	openstack_helm.HelmValues `yaml:"__neutron_helm_values"`
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
		"bagpipe_bgp": "high-priority",
		"bgp_dragent": "high-priority",
		"db_sync": "high-priority",
		"neutron_dhcp_agent": "high-priority",
		"neutron_l2gw_agent": "high-priority",
		"neutron_l3_agent": "high-priority",
		"neutron_lb_agent": "high-priority",
		"neutron_metadata_agent": "high-priority",
		"neutron_netns_cleanup_cron": "high-priority",
		"ovn_vpn_agent": "high-priority",
		"neutron_ovn_metadata_agent": "high-priority",
		"neutron_ovs_agent": "high-priority",
		"neutron_sriov_agent": "high-priority",
		"neutron_ironic_agent": "high-priority",
		"neutron_rpc_server": "high-priority",
		"neutron_server": "high-priority",
		"neutron_tests": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"bootstrap": "kata-clh",
		"bagpipe_bgp": "kata-clh",
		"bgp_dragent": "kata-clh",
		"db_sync": "kata-clh",
		"neutron_dhcp_agent": "kata-clh",
		"neutron_l2gw_agent": "kata-clh",
		"neutron_l3_agent": "kata-clh",
		"neutron_lb_agent": "kata-clh",
		"neutron_metadata_agent": "kata-clh",
		"neutron_netns_cleanup_cron": "kata-clh",
		"ovn_vpn_agent": "kata-clh",
		"neutron_ovn_metadata_agent": "kata-clh",
		"neutron_ovs_agent": "kata-clh",
		"neutron_sriov_agent": "kata-clh",
		"neutron_ironic_agent": "kata-clh",
		"neutron_rpc_server": "kata-clh",
		"neutron_server": "kata-clh",
		"neutron_tests": "kata-clh",
	}
	vals, err := openstack_helm.CoalescedHelmValues("../../charts/neutron", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Neutron.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}
