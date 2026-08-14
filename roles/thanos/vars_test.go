package thanos

import (
	_ "embed"
	"os"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

var (
	//go:embed defaults/main.yml
	defaultsFile []byte

	//go:embed vars/main.yml
	varsFile []byte
)

type resources struct {
	Requests map[string]string `yaml:"requests"`
	Limits   map[string]string `yaml:"limits"`
}

type rollingUpdate struct {
	MaxSurge       int `yaml:"maxSurge"`
	MaxUnavailable int `yaml:"maxUnavailable"`
}

type updateStrategy struct {
	Type          string        `yaml:"type"`
	RollingUpdate rollingUpdate `yaml:"rollingUpdate"`
}

type defaults struct {
	QueryReplicas            int            `yaml:"thanos_query_replicas"`
	QueryFrontendReplicas    int            `yaml:"thanos_query_frontend_replicas"`
	StoreGatewayReplicas     int            `yaml:"thanos_store_gateway_replicas"`
	PodAntiAffinityPreset    string         `yaml:"thanos_pod_anti_affinity_preset"`
	PDBMinAvailable          int            `yaml:"thanos_pdb_min_available"`
	DeploymentUpdateStrategy updateStrategy `yaml:"thanos_deployment_update_strategy"`
	QueryResources           resources      `yaml:"thanos_query_resources"`
	QueryFrontendResources   resources      `yaml:"thanos_query_frontend_resources"`
	StoreGatewayResources    resources      `yaml:"thanos_store_gateway_resources"`
	CompactorResources       resources      `yaml:"thanos_compactor_resources"`
}

func nestedMap(t *testing.T, value map[string]interface{}, key string) map[string]interface{} {
	t.Helper()

	nested, ok := value[key].(map[string]interface{})
	require.True(t, ok, "%s is not a map", key)

	return nested
}

func TestProductionDefaults(t *testing.T) {
	var values defaults
	require.NoError(t, yaml.Unmarshal(defaultsFile, &values))

	assert.Equal(t, 3, values.QueryReplicas)
	assert.Equal(t, 3, values.QueryFrontendReplicas)
	assert.Equal(t, 3, values.StoreGatewayReplicas)
	assert.Equal(t, "hard", values.PodAntiAffinityPreset)
	assert.Equal(t, 2, values.PDBMinAvailable)
	assert.Equal(t, "RollingUpdate", values.DeploymentUpdateStrategy.Type)
	assert.Equal(t, 0, values.DeploymentUpdateStrategy.RollingUpdate.MaxSurge)
	assert.Equal(t, 1, values.DeploymentUpdateStrategy.RollingUpdate.MaxUnavailable)

	for name, resources := range map[string]resources{
		"query":          values.QueryResources,
		"query-frontend": values.QueryFrontendResources,
		"store-gateway":  values.StoreGatewayResources,
		"compactor":      values.CompactorResources,
	} {
		t.Run(name, func(t *testing.T) {
			assert.NotEmpty(t, resources.Requests["cpu"])
			assert.NotEmpty(t, resources.Requests["memory"])
			assert.NotEmpty(t, resources.Limits["cpu"])
			assert.NotEmpty(t, resources.Limits["memory"])
		})
	}
}

func TestProductionDefaultsAreWiredIntoHelmValues(t *testing.T) {
	var root map[string]interface{}
	require.NoError(t, yaml.Unmarshal(varsFile, &root))

	values := nestedMap(t, root, "_thanos_helm_values")
	components := map[string]string{
		"query":         "{{ thanos_query_resources }}",
		"queryFrontend": "{{ thanos_query_frontend_resources }}",
		"storegateway":  "{{ thanos_store_gateway_resources }}",
		"compactor":     "{{ thanos_compactor_resources }}",
	}

	for name, expectedResources := range components {
		t.Run(name, func(t *testing.T) {
			component := nestedMap(t, values, name)
			assert.Equal(t, expectedResources, component["resources"])

			if name == "compactor" {
				return
			}

			assert.Equal(t, "{{ thanos_pod_anti_affinity_preset }}", component["podAntiAffinityPreset"])
			pdb := nestedMap(t, component, "pdb")
			assert.Equal(t, true, pdb["create"])
			assert.Equal(t, "{{ thanos_pdb_min_available }}", pdb["minAvailable"])
		})
	}

	for _, name := range []string{"query", "queryFrontend"} {
		component := nestedMap(t, values, name)
		assert.Equal(t, "{{ thanos_deployment_update_strategy }}", component["updateStrategy"])
	}
}

func TestKubePrometheusStackDiscoveryUsesConfiguredRelease(t *testing.T) {
	var root map[string]interface{}
	require.NoError(t, yaml.Unmarshal(varsFile, &root))

	values := nestedMap(t, root, "_thanos_helm_values")
	query := nestedMap(t, values, "query")
	discovery := nestedMap(t, query, "dnsDiscovery")
	assert.Equal(t, "{{ kube_prometheus_stack_helm_release_name }}-thanos-discovery", discovery["sidecarsService"])
	assert.Equal(t, "{{ kube_prometheus_stack_helm_release_namespace }}", discovery["sidecarsNamespace"])

	metrics := nestedMap(t, values, "metrics")
	serviceMonitor := nestedMap(t, metrics, "serviceMonitor")
	labels := nestedMap(t, serviceMonitor, "labels")
	assert.Equal(t, "{{ kube_prometheus_stack_helm_release_name }}", labels["release"])
}

func TestAllInOneOverrides(t *testing.T) {
	moleculeFile, err := os.ReadFile("../../molecule/shared/molecule.yml")
	require.NoError(t, err)

	var root map[string]interface{}
	require.NoError(t, yaml.Unmarshal(moleculeFile, &root))

	provisioner := nestedMap(t, root, "provisioner")
	inventory := nestedMap(t, provisioner, "inventory")
	groupVars := nestedMap(t, inventory, "group_vars")
	all := nestedMap(t, groupVars, "all")

	assert.Equal(t, uint64(1), all["thanos_query_replicas"])
	assert.Equal(t, uint64(1), all["thanos_query_frontend_replicas"])
	assert.Equal(t, uint64(1), all["thanos_store_gateway_replicas"])
	assert.Equal(t, "soft", all["thanos_pod_anti_affinity_preset"])
	assert.Equal(t, uint64(0), all["thanos_pdb_min_available"])
	assert.Equal(t, "5Gi", all["thanos_store_gateway_storage_size"])
	assert.Equal(t, "10Gi", all["thanos_compactor_storage_size"])
}
