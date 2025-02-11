package percona_xtradb_cluster

import (
	_ "embed"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"strings"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/vexxhost/atmosphere/roles/defaults"
	"gopkg.in/ini.v1"
	"helm.sh/helm/v3/pkg/chart/loader"
	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"

	pxc_v1 "github.com/percona/percona-xtradb-cluster-operator/pkg/apis/pxc/v1"
)

var (
	//go:embed vars/main.yml
	varsFile []byte
	vars     Vars
)

type Vars struct {
	PerconaXtraDBClusterSpec pxc_v1.PerconaXtraDBClusterSpec `yaml:"_percona_xtradb_cluster_spec"`
}

func TestMain(m *testing.M) {
	t := &testing.T{}

	err := yaml.UnmarshalWithOptions(varsFile, &vars, yaml.Strict(), yaml.UseJSONUnmarshaler())
	require.NoError(t, err)

	code := m.Run()
	os.Exit(code)
}

func TestPerconaXtraDBClusterSpec(t *testing.T) {
	chart, err := loader.LoadDir("../../charts/pxc-operator")
	require.NoError(t, err)

	assert.Equal(t, chart.AppVersion(), vars.PerconaXtraDBClusterSpec.CRVersion)
	assert.Equal(t, "percona-xtradb", vars.PerconaXtraDBClusterSpec.SecretsName)
}

func TestPerconaXtraDBClusterPXCSpec(t *testing.T) {
	assert.Equal(t, int32(3), vars.PerconaXtraDBClusterSpec.PXC.Size)
	assert.Equal(t, true, *vars.PerconaXtraDBClusterSpec.PXC.AutoRecovery)
	defaults.AssertAtmosphereImage(t, "docker.io/percona/percona-xtradb-cluster:8.0.36-28.1", vars.PerconaXtraDBClusterSpec.PXC.Image)

	assert.Equal(t, map[string]string{
		"openstack-control-plane": "enabled",
	}, vars.PerconaXtraDBClusterSpec.PXC.NodeSelector)

	assert.Equal(t, &pxc_v1.VolumeSpec{
		PersistentVolumeClaim: &v1.PersistentVolumeClaimSpec{
			Resources: v1.VolumeResourceRequirements{
				Requests: v1.ResourceList{
					"storage": resource.MustParse("160Gi"),
				},
			},
		},
	}, vars.PerconaXtraDBClusterSpec.PXC.VolumeSpec)
}

func parsePXCConfiguration(t *testing.T, cfg string) *ini.File {
	parsed, err := ini.LoadSources(ini.LoadOptions{
		AllowBooleanKeys:          true,
		UnescapeValueDoubleQuotes: true,
	}, []byte(cfg))
	require.NoError(t, err)

	return parsed
}

func TestPerconaXtraDBClusterPXCConfiguration(t *testing.T) {
	cfg := parsePXCConfiguration(t, vars.PerconaXtraDBClusterSpec.PXC.Configuration)

	section := cfg.Section("mysqld")
	assert.Len(t, section.Keys(), 16)

	assert.Equal(t, "{{ percona_xtradb_cluster_innodb_buffer_pool_size }}", section.Key("innodb_buffer_pool_size").String())
	assert.Equal(t, "128M", section.Key("innodb_log_buffer_size").String())
	assert.Equal(t, "1G", section.Key("innodb_log_file_size").String())
	assert.Equal(t, 8, section.Key("innodb_read_io_threads").MustInt())
	assert.Equal(t, 8, section.Key("innodb_write_io_threads").MustInt())
	assert.Equal(t, "16M", section.Key("max_allowed_packet").String())
	assert.Equal(t, 10000, section.Key("max_connect_errors").MustInt())
	assert.Equal(t, 8192, section.Key("max_connections").MustInt())
	assert.Equal(t, "64M", section.Key("max_heap_table_size").String())
	assert.Equal(t, "derived_merge=off", section.Key("optimizer_switch").String())
	assert.Equal(t, "MASTER", section.Key("pxc_strict_mode").String())
	assert.Equal(t, "ON", section.Key("skip_name_resolve").String())
	assert.Equal(t, "64M", section.Key("tmp_table_size").String())
	assert.Equal(t, "evs.suspect_timeout=PT30S; gcache.size=2G; gcomm.thread_prio=rr:2; gcs.fc_factor=0.8; gcs.fc_limit=160; gmcast.peer_timeout=PT15S", section.Key("wsrep_provider_options").String())
	assert.Equal(t, 3, section.Key("wsrep_retry_autocommit").MustInt())
	assert.Equal(t, 16, section.Key("wsrep_slave_threads").MustInt())
}

func TestPerconaXtraDBClusterPXCSidecarSpec(t *testing.T) {
	sidecar := vars.PerconaXtraDBClusterSpec.PXC.Sidecars[0]
	assert.Equal(t, "exporter", sidecar.Name)
	defaults.AssertAtmosphereImage(t, "quay.io/prometheus/mysqld-exporter:v0.15.1", sidecar.Image)

	assert.Equal(t, v1.EnvVar{
		Name: "MYSQLD_EXPORTER_PASSWORD",
		ValueFrom: &v1.EnvVarSource{
			SecretKeyRef: &v1.SecretKeySelector{
				LocalObjectReference: v1.LocalObjectReference{
					Name: vars.PerconaXtraDBClusterSpec.SecretsName,
				},
				Key: "monitor",
			},
		},
	}, sidecar.Env[0])

	assert.Equal(t, v1.ContainerPort{
		Name:          "metrics",
		ContainerPort: 9104,
	}, sidecar.Ports[0])
}

func TestPerconaXtraDBClusterHAProxySpec(t *testing.T) {
	assert.Equal(t, true, vars.PerconaXtraDBClusterSpec.HAProxy.Enabled)
	assert.Equal(t, int32(3), vars.PerconaXtraDBClusterSpec.HAProxy.Size)

	defaults.AssertAtmosphereImage(t,
		fmt.Sprintf("docker.io/percona/percona-xtradb-cluster-operator:%s-haproxy", vars.PerconaXtraDBClusterSpec.CRVersion),
		vars.PerconaXtraDBClusterSpec.HAProxy.Image,
	)

	assert.Equal(t, map[string]string{
		"openstack-control-plane": "enabled",
	}, vars.PerconaXtraDBClusterSpec.HAProxy.NodeSelector)
}

func TestPerconaXtraDBClusterHAProxyConfiguration(t *testing.T) {
	pxcConfig := parsePXCConfiguration(t, vars.PerconaXtraDBClusterSpec.PXC.Configuration)
	maxConnections := pxcConfig.Section("mysqld").Key("max_connections").MustInt()

	// NOTE(mnaser): Since there is no way of overriding specific values, we pull
	//               the file from the Docker image, replace the maxconn value and
	//               then compare it.

	// Get the default HAproxy configuration
	configFileUrl := fmt.Sprintf("https://raw.githubusercontent.com/percona/percona-docker/pxc-operator-%s/haproxy/dockerdir/etc/haproxy/haproxy-global.cfg", vars.PerconaXtraDBClusterSpec.CRVersion)
	resp, err := http.Get(configFileUrl)
	require.NoError(t, err)
	defer resp.Body.Close()
	haproxyConfigData, err := io.ReadAll(resp.Body)
	require.NoError(t, err)
	haproxyConfig := string(haproxyConfigData)

	// Replace the 4 spaces at the start of each line
	regex := regexp.MustCompile("(?m)^    ")
	haproxyConfig = regex.ReplaceAllString(haproxyConfig, "")

	// Replace the maxconn value
	haproxyConfig = strings.Replace(haproxyConfig, "maxconn 2048", fmt.Sprintf("maxconn %d", maxConnections), 1)
	assert.Contains(t, haproxyConfig, fmt.Sprintf("maxconn %d", maxConnections))

	assert.Equal(t,
		haproxyConfig,
		vars.PerconaXtraDBClusterSpec.HAProxy.Configuration,
	)
}
