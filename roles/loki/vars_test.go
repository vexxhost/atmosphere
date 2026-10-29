package loki

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
	AlertRulesConfigMap   map[string]any    `yaml:"_loki_alert_rules_configmap"`
	DefaultAlertRuleFiles map[string]string `yaml:"_loki_default_alert_rule_files"`
}

func TestMain(m *testing.M) {
	t := &testing.T{}
	err := yaml.UnmarshalWithOptions(varsFile, &vars)
	require.NoError(t, err)

	code := m.Run()
	os.Exit(code)
}

func TestDefaultAlertRuleFiles(t *testing.T) {
	defaultRules, ok := vars.DefaultAlertRuleFiles["loki-alerting-rules.yaml"]
	require.True(t, ok)
	assert.Contains(t, defaultRules, "NovaCellNotResponding")
}

func TestAlertRulesConfigMapKeepAnnotation(t *testing.T) {
	metadata, ok := vars.AlertRulesConfigMap["metadata"].(map[string]any)
	require.True(t, ok)

	annotations, ok := metadata["annotations"].(map[string]any)
	require.True(t, ok)
	assert.Equal(t, "keep", annotations["helm.sh/resource-policy"])
}

func TestCustomAlertRuleFilesMerge(t *testing.T) {
	customRuleFiles := map[string]string{
		"julian-rules.yaml": "groups:\n  - name: julian-rules\n",
	}

	mergedRuleFiles := make(map[string]string, len(vars.DefaultAlertRuleFiles)+len(customRuleFiles))
	for name, contents := range vars.DefaultAlertRuleFiles {
		mergedRuleFiles[name] = contents
	}
	for name, contents := range customRuleFiles {
		mergedRuleFiles[name] = contents
	}

	assert.Contains(t, mergedRuleFiles, "loki-alerting-rules.yaml")
	assert.Contains(t, mergedRuleFiles, "julian-rules.yaml")
	assert.Contains(t, mergedRuleFiles["loki-alerting-rules.yaml"], "NovaCellNotResponding")
	assert.Contains(t, mergedRuleFiles["julian-rules.yaml"], "julian-rules")
}
