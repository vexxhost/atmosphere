package keycloak

import (
	_ "embed"
	"net/url"
	"strings"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/require"
)

//go:embed vars/main.yml
var varsFile []byte

func TestDatabaseCausalReads(t *testing.T) {
	var vars struct {
		HelmValues struct {
			ExtraEnvVars []struct {
				Name  string `yaml:"name"`
				Value string `yaml:"value"`
			} `yaml:"extraEnvVars"`
		} `yaml:"_keycloak_helm_values"`
	}
	require.NoError(t, yaml.Unmarshal(varsFile, &vars))

	for _, env := range vars.HelmValues.ExtraEnvVars {
		if env.Name != "KC_DB_URL" {
			continue
		}
		connection := strings.NewReplacer(
			"{{ openstack_helm_endpoints.oslo_db.hosts.default }}", "database",
			"{{ keycloak_database_name }}", "identity",
		).Replace(env.Value)
		parsed, err := url.Parse(strings.TrimPrefix(connection, "jdbc:"))
		require.NoError(t, err)
		require.Equal(t, "database.openstack:3306", parsed.Host)
		require.Equal(t, "/identity", parsed.Path)
		require.Equal(t, "wsrep_sync_wait=1", parsed.Query().Get("sessionVariables"))
		return
	}
	t.Fatal("KC_DB_URL is missing")
}
