package octavia

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/require"
	"helm.sh/helm/v3/pkg/chart/loader"
	"helm.sh/helm/v3/pkg/chartutil"
	"helm.sh/helm/v3/pkg/engine"
)

func TestHealthManagerMTU(t *testing.T) {
	chart, err := loader.Load("../../charts/octavia")
	require.NoError(t, err)
	values, err := chartutil.ToRenderValues(chart, map[string]interface{}{}, chartutil.ReleaseOptions{
		Name:      "octavia",
		Namespace: "openstack",
		IsInstall: true,
	}, chartutil.DefaultCapabilities)
	require.NoError(t, err)
	rendered, err := engine.Render(chart, values)
	require.NoError(t, err)

	var configMap struct {
		Data map[string]string `yaml:"data"`
	}
	require.NoError(t, yaml.Unmarshal([]byte(rendered["octavia/templates/configmap-bin.yaml"]), &configMap))
	getPort := configMap.Data["octavia-health-manager-get-port.sh"]
	nicInit := configMap.Data["octavia-health-manager-nic-init.sh"]
	require.NotEmpty(t, getPort)
	require.NotEmpty(t, nicInit)
	require.Contains(t, configMap.Data["octavia-health-manager.sh"], "request subnet-mask,broadcast-address,interface-mtu;")
	require.NotContains(t, configMap.Data["octavia-health-manager.sh"], "supersede interface-mtu")

	for _, tc := range []struct {
		name        string
		mtu         string
		failedQuery string
		wantError   bool
	}{
		{name: "standard", mtu: "1500"},
		{name: "overlay", mtu: "8942"},
		{name: "jumbo", mtu: "9000"},
		{name: "missing", mtu: "", wantError: true},
		{name: "zero", mtu: "0", wantError: true},
		{name: "null", mtu: "None", wantError: true},
		{name: "nonnumeric", mtu: "invalid", wantError: true},
		{name: "negative", mtu: "-1", wantError: true},
		{name: "too-small", mtu: "67", wantError: true},
		{name: "too-large", mtu: "65536", wantError: true},
		{name: "overflow", mtu: "18446744073709553116", wantError: true},
		{name: "port-query-failure", mtu: "9000", failedQuery: "port", wantError: true},
		{name: "network-query-failure", mtu: "9000", failedQuery: "network", wantError: true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			dir := t.TempDir()
			shared := filepath.Join(dir, "pod-shared")
			require.NoError(t, os.Mkdir(shared, 0755))
			calls := filepath.Join(dir, "calls")
			require.NoError(t, os.WriteFile(calls, nil, 0644))

			commands := map[string]string{
				"openstack": `#!/bin/bash
set -eu
printf 'openstack %s\n' "$*" >> "$MTU_TEST_CALLS"
if [[ $1 == "$MTU_TEST_FAILED_QUERY" ]]; then
    exit 1
fi
case "$1 $2" in
    'port show')
        case "$5" in
            id) echo port-id ;;
            mac_address) echo fa:16:3e:00:00:01 ;;
            network_id) echo port-network-id ;;
            *) exit 1 ;;
        esac ;;
    'network show')
        [[ $3 == port-network-id && $5 == mtu ]]
        printf '%s\n' "$MTU_TEST_VALUE" ;;
    *) exit 1 ;;
esac
`,
				"ovs-vsctl": `#!/bin/bash
printf 'ovs-vsctl %s\n' "$*" >> "$MTU_TEST_CALLS"
`,
				"ip": `#!/bin/bash
printf 'ip %s\n' "$*" >> "$MTU_TEST_CALLS"
`,
				"iptables": `#!/bin/bash
printf 'iptables %s\n' "$*" >> "$MTU_TEST_CALLS"
`,
			}
			for name, script := range commands {
				require.NoError(t, os.WriteFile(filepath.Join(dir, name), []byte(script), 0755))
			}

			run := func(script string) (string, error) {
				cmd := exec.Command("bash", "-c", strings.ReplaceAll(script, "/tmp/pod-shared", shared))
				cmd.Env = append(os.Environ(),
					"PATH="+dir+string(os.PathListSeparator)+os.Getenv("PATH"),
					"MTU_TEST_CALLS="+calls,
					"MTU_TEST_VALUE="+tc.mtu,
					"MTU_TEST_FAILED_QUERY="+tc.failedQuery,
				)
				output, err := cmd.CombinedOutput()
				return string(output), err
			}

			output, err := run(getPort)
			mtuFile := filepath.Join(shared, "HM_PORT_MTU")
			if tc.wantError {
				require.Error(t, err, output)
				require.NoFileExists(t, mtuFile)
				if tc.failedQuery == "" {
					require.Contains(t, output, "Invalid Octavia management network MTU")
				}
				return
			}
			require.NoError(t, err, output)
			mtu, err := os.ReadFile(mtuFile)
			require.NoError(t, err)
			require.Equal(t, tc.mtu+"\n", string(mtu))

			output, err = run(nicInit)
			require.NoError(t, err, output)
			log, err := os.ReadFile(calls)
			require.NoError(t, err)
			require.Contains(t, string(log), "openstack network show port-network-id -c mtu -f value\n")
			require.Contains(t, string(log), "-- set Interface o-hm0 mtu_request="+tc.mtu+"\n")
			require.NotContains(t, string(log), "ip link set dev o-hm0 mtu")
		})
	}
}
