package kube_prometheus_stack

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/google/go-jsonnet"
	"github.com/stretchr/testify/require"
)

func TestPrometheusRules(t *testing.T) {
	// Create a Jsonnet VM
	vm := jsonnet.MakeVM()

	// Set up the import path for vendor libraries
	vm.Importer(&jsonnet.FileImporter{
		JPaths: []string{
			"files/jsonnet",
			"files/jsonnet/vendor",
		},
	})

	// Evaluate the rules.jsonnet file
	jsonStr, err := vm.EvaluateFile("files/jsonnet/rules.jsonnet")
	require.NoError(t, err, "failed to evaluate jsonnet file")

	// Parse the JSON output into a map of rule groups
	var rules map[string]interface{}
	err = json.Unmarshal([]byte(jsonStr), &rules)
	require.NoError(t, err, "failed to parse jsonnet output")

	// Create a temporary directory for rule files
	tempDir, err := os.MkdirTemp("", "prometheus-rules-*")
	require.NoError(t, err)
	defer os.RemoveAll(tempDir)

	// Write each rule group to a separate YAML file
	var ruleFiles []string
	for name, rule := range rules {
		filePath := filepath.Join(tempDir, name+".yaml")

		ruleData, err := yaml.Marshal(rule)
		require.NoError(t, err, "failed to marshal rule %s", name)

		err = os.WriteFile(filePath, ruleData, 0644)
		require.NoError(t, err, "failed to write rule file %s", name)

		ruleFiles = append(ruleFiles, filePath)
	}

	// Read the tests.yml file
	testsData, err := os.ReadFile("files/jsonnet/tests.yml")
	require.NoError(t, err, "failed to read tests.yml")

	// Parse tests.yml
	var tests map[string]interface{}
	err = yaml.Unmarshal(testsData, &tests)
	require.NoError(t, err, "failed to parse tests.yml")

	// Add the rule_files to the tests config
	tests["rule_files"] = ruleFiles

	// Write the complete tests config
	testsFilePath := filepath.Join(tempDir, "tests.yaml")
	testsOutput, err := yaml.Marshal(tests)
	require.NoError(t, err, "failed to marshal tests config")

	err = os.WriteFile(testsFilePath, testsOutput, 0644)
	require.NoError(t, err, "failed to write tests config")

	// Run promtool test rules
	cmd := exec.Command("promtool", "test", "rules", testsFilePath)
	output, err := cmd.CombinedOutput()
	require.NoError(t, err, "promtool failed: %s", string(output))
}
