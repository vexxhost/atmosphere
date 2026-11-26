package neutron

import (
	_ "embed"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

var (
	//go:embed tasks/network.yml
	networkTasksFile []byte
)

func TestNetworkResourceTasks(t *testing.T) {
	var tasks []map[string]any
	require.NoError(t, yaml.UnmarshalWithOptions(networkTasksFile, &tasks, yaml.Strict()))

	var createSubnetTask map[string]any
	for _, task := range tasks {
		if task["name"] == "Create subnets" {
			createSubnetTask = task
			break
		}
	}
	require.NotNil(t, createSubnetTask)

	createSubnet, ok := createSubnetTask["vexxhost.atmosphere.subnet"].(map[string]any)
	require.True(t, ok)
	assert.Equal(t, "{{ _neutron_network_result.id }}", createSubnet["network"])
	assert.Equal(
		t,
		"{{ subnet.project | default(neutron_network.project | default(omit)) }}",
		createSubnet["project"],
	)
}
