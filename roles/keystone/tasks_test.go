package keystone

import (
	_ "embed"
	"os"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Create Keycloak realms

var (
	//go:embed tasks/main.yml
	tasksFile []byte
	tasks     []map[string]interface{}
)

func TestMain(m *testing.M) {
	t := &testing.T{}

	err := yaml.UnmarshalWithOptions(tasksFile, &tasks, yaml.Strict())
	require.NoError(t, err)

	code := m.Run()
	os.Exit(code)
}

func getTaskByName(name string) map[string]interface{} {
	for _, t := range tasks {
		if t["name"] == name {
			return t
		}
	}
	return nil
}

func TestCreateKeycloakRealmsTask(t *testing.T) {
	task := getTaskByName("Create Keycloak realms")
	require.NotNil(t, task)

	assert.Equal(t, true, task["no_log"])
	assert.Equal(t, false, task["become"])
}

func TestCreateKeycloakClientsTask(t *testing.T) {
	task := getTaskByName("Create Keycloak clients")
	require.NotNil(t, task)

	assert.Equal(t, true, task["no_log"])
	assert.Equal(t, false, task["become"])
}
