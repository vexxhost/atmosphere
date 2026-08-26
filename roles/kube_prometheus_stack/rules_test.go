package kube_prometheus_stack

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/google/go-jsonnet"
	"github.com/stretchr/testify/require"
)

func TestPrometheusRules(t *testing.T) {
	vm := jsonnet.MakeVM()
	vm.Importer(&jsonnet.FileImporter{
		JPaths: []string{"files/jsonnet", "files/jsonnet/vendor"},
	})

	jsonStr, err := vm.EvaluateFile("files/jsonnet/rules.jsonnet")
	require.NoError(t, err, "failed to evaluate jsonnet file")

	var rules map[string]any
	require.NoError(t, json.Unmarshal([]byte(jsonStr), &rules), "failed to parse jsonnet output")

	dns1123Subdomain := regexp.MustCompile(`^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$`)
	for name := range rules {
		require.LessOrEqual(t, len(name), 253, "rule map key %q exceeds the DNS subdomain limit", name)
		require.Regexp(t, dns1123Subdomain, name, "rule map key %q must be a DNS-1123 subdomain", name)
	}

	tempDir := t.TempDir()

	ruleFiles := make([]string, 0, len(rules))
	for name, rule := range rules {
		filePath := filepath.Join(tempDir, name+".yaml")
		ruleData, err := yaml.Marshal(rule)
		require.NoError(t, err, "failed to marshal rule %s", name)
		require.NoError(t, os.WriteFile(filePath, ruleData, 0644), "failed to write rule file %s", name)
		ruleFiles = append(ruleFiles, filePath)
	}

	testsData, err := os.ReadFile("files/jsonnet/tests.yml")
	require.NoError(t, err, "failed to read tests.yml")

	var testsConfig struct {
		Tests []map[string]any `yaml:"tests"`
	}
	require.NoError(t, yaml.Unmarshal(testsData, &testsConfig), "failed to parse tests.yml")

	for i, testCase := range testsConfig.Tests {
		testName := fmt.Sprintf("test_%d", i)
		if alertTests, ok := testCase["alert_rule_test"].([]any); ok && len(alertTests) > 0 {
			if firstAlert, ok := alertTests[0].(map[string]any); ok {
				if name, ok := firstAlert["alertname"].(string); ok {
					testName = name
				}
			}
		}

		t.Run(testName, func(t *testing.T) {
			t.Parallel()

			testConfig := map[string]any{
				"rule_files": ruleFiles,
				"tests":      []map[string]any{testCase},
			}

			testConfigPath := filepath.Join(tempDir, fmt.Sprintf("test_%d.yaml", i))
			testOutput, err := yaml.Marshal(testConfig)
			require.NoError(t, err, "failed to marshal test config")
			require.NoError(t, os.WriteFile(testConfigPath, testOutput, 0644), "failed to write test config")

			output, err := exec.Command("promtool", "test", "rules", testConfigPath).CombinedOutput()
			require.NoError(t, err, "promtool failed: %s", string(output))
		})
	}
}
