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

	vals, err := openstack_helm.CoalescedHelmValues("../../charts/keystone", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Keystone.Database)
}
