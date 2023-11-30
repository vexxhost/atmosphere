package senlin

import (
	_ "embed"
	"os"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

var (
	//go:embed vars/main.yml
	varsFile []byte
	vars     Vars
)

type Vars struct {
	SenlinHelmValues `yaml:"_senlin_helm_values"`
}

type SenlinHelmValues struct {
	Conf `yaml:"conf"`
}

type Conf struct {
	Senlin SenlinConf `yaml:"senlin"`
}

type SenlinConf struct {
	API SenlinAPIConf `yaml:"senlin_api"`
}

type SenlinAPIConf struct {
	Workers int32 `yaml:"workers"`
}

func TestMain(m *testing.M) {
	t := &testing.T{}
	err := yaml.UnmarshalWithOptions(varsFile, &vars)
	require.NoError(t, err)

	code := m.Run()
	os.Exit(code)
}

func TestSenlinHelmValues(t *testing.T) {
	assert.Equal(t, int32(2), vars.SenlinHelmValues.Conf.Senlin.API.Workers)
}
