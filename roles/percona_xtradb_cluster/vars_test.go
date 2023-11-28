package percona_xtradb_cluster

import (
	_ "embed"
	"fmt"
	"os"
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
	vars_file []byte
	vars      Vars
)

type Vars struct {
	PerconaXtraDBClusterSpec pxc_v1.PerconaXtraDBClusterSpec `yaml:"_percona_xtradb_cluster_spec"`
}

func TestMain(m *testing.M) {
	t := &testing.T{}

	err := yaml.UnmarshalWithOptions(vars_file, &vars, yaml.Strict(), yaml.UseJSONUnmarshaler())
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
	defaults.AssertAtmosphereImage(t, "docker.io/percona/percona-xtradb-cluster:5.7.39-31.61", vars.PerconaXtraDBClusterSpec.PXC.Image)

	assert.Equal(t, map[string]string{
		"openstack-control-plane": "enabled",
	}, vars.PerconaXtraDBClusterSpec.PXC.NodeSelector)

	assert.Equal(t, &pxc_v1.VolumeSpec{
		PersistentVolumeClaim: &v1.PersistentVolumeClaimSpec{
			Resources: v1.ResourceRequirements{
				Requests: v1.ResourceList{
					"storage": resource.MustParse("160Gi"),
				},
			},
		},
	}, vars.PerconaXtraDBClusterSpec.PXC.VolumeSpec)
}

func TestPerconaXtraDBClusterPXCConfiguration(t *testing.T) {
	cfg, err := ini.LoadSources(ini.LoadOptions{
		AllowBooleanKeys: true,
	}, []byte(vars.PerconaXtraDBClusterSpec.PXC.Configuration))
	require.NoError(t, err)

	section := cfg.Section("mysqld")
	assert.Equal(t, 8192, section.Key("max_connections").MustInt())
	assert.Equal(t, "4096M", section.Key("innodb_buffer_pool_size").String())
	assert.Equal(t, "16M", section.Key("max_allowed_packet").String())
	assert.Equal(t, true, section.Key("skip-name-resolve").MustBool())
}

func TestPerconaXtraDBClusterPXCSidecarSpec(t *testing.T) {
	sidecar := vars.PerconaXtraDBClusterSpec.PXC.Sidecars[0]
	assert.Equal(t, "exporter", sidecar.Name)
	defaults.AssertAtmosphereImage(t, "quay.io/prometheus/mysqld-exporter:v0.14.0", sidecar.Image)

	assert.Equal(t, v1.EnvVar{
		Name: "MONITOR_PASSWORD",
		ValueFrom: &v1.EnvVarSource{
			SecretKeyRef: &v1.SecretKeySelector{
				LocalObjectReference: v1.LocalObjectReference{
					Name: vars.PerconaXtraDBClusterSpec.SecretsName,
				},
				Key: "monitor",
			},
		},
	}, sidecar.Env[0])
	assert.Equal(t, v1.EnvVar{
		Name:  "DATA_SOURCE_NAME",
		Value: "monitor:$(MONITOR_PASSWORD)@(localhost:3306)/",
	}, sidecar.Env[1])

	assert.Equal(t, v1.ContainerPort{
		Name:          "metrics",
		ContainerPort: 9104,
	}, sidecar.Ports[0])
}

func TestPerconaXtraDBClusterHAProxySpec(t *testing.T) {
	assert.Equal(t, true, vars.PerconaXtraDBClusterSpec.HAProxy.Enabled)
	assert.Equal(t, int32(3), vars.PerconaXtraDBClusterSpec.HAProxy.Size)

	chart, err := loader.LoadDir("../../charts/pxc-operator")
	require.NoError(t, err)

	defaults.AssertAtmosphereImage(t,
		fmt.Sprintf("docker.io/percona/percona-xtradb-cluster-operator:%s-haproxy", chart.AppVersion()),
		vars.PerconaXtraDBClusterSpec.HAProxy.Image,
	)

	assert.Equal(t, map[string]string{
		"openstack-control-plane": "enabled",
	}, vars.PerconaXtraDBClusterSpec.HAProxy.NodeSelector)
}
