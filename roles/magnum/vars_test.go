package magnum

import (
	_ "embed"
	"os"
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
	openstack_helm.HelmValues `yaml:"_magnum_helm_values"`
	MagnumImages              []MagnumImage `yaml:"_magnum_images"`
}

type MagnumImage struct {
	Name   string `yaml:"name"`
	URL    string `yaml:"url"`
	Distro string `yaml:"distro"`
}

func TestMain(m *testing.M) {
	t := &testing.T{}
	err := yaml.UnmarshalWithOptions(varsFile, &vars)
	require.NoError(t, err)

	code := m.Run()
	os.Exit(code)
}

func TestHelmValues(t *testing.T) {
	// (rlin): Before you add any new priority class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_priority_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_priority_class" }}
	vars.HelmValues.Pod.PriorityClass = map[string]string{
		"bootstrap":        "high-priority",
		"db_sync":          "high-priority",
		"magnum_api":       "high-priority",
		"magnum_conductor": "high-priority",
	}
	// (rlin): Before you add any new runtime class here.
	// Make sure we do use snippets tool
	// helm-toolkit.snippets.kubernetes_pod_runtime_class
	// for the actual template. Like:
	// {{ tuple "heat_api" . | include "helm-toolkit.snippets.kubernetes_pod_runtime_class" }}
	vars.HelmValues.Pod.RuntimeClass = map[string]string{
		"bootstrap":        "kata-clh",
		"db_sync":          "kata-clh",
		"magnum_api":       "kata-clh",
		"magnum_conductor": "kata-clh",
	}
	vals, err := openstack_helm.CoalescedHelmValues("../../charts/magnum", &vars.HelmValues)
	require.NoError(t, err)

	testutils.TestDatabaseConf(t, vals.Conf.Magnum.Database)
	testutils.TestAllPodsHaveRuntimeClass(t, vals)
	testutils.TestAllPodsHavePriorityClass(t, vals)
}

func TestMagnumImages(t *testing.T) {
	require.Equal(t, []MagnumImage{
		{
			Name:   "ubuntu-2404-kube-v1.33.12",
			URL:    "https://github.com/vexxhost/capo-image-elements/releases/download/2026.05-7/ubuntu-24.04-v1.33.12.qcow2",
			Distro: "ubuntu",
		},
		{
			Name:   "ubuntu-2404-kube-v1.34.8",
			URL:    "https://github.com/vexxhost/capo-image-elements/releases/download/2026.05-7/ubuntu-24.04-v1.34.8.qcow2",
			Distro: "ubuntu",
		},
		{
			Name:   "ubuntu-2404-kube-v1.35.5",
			URL:    "https://github.com/vexxhost/capo-image-elements/releases/download/2026.05-7/ubuntu-24.04-v1.35.5.qcow2",
			Distro: "ubuntu",
		},
		{
			Name:   "ubuntu-2404-kube-v1.36.1",
			URL:    "https://github.com/vexxhost/capo-image-elements/releases/download/2026.05-7/ubuntu-24.04-v1.36.1.qcow2",
			Distro: "ubuntu",
		},
	}, vars.MagnumImages)
}
