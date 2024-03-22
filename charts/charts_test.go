package charts

import (
	"io"
	"os"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/yannh/kubeconform/pkg/validator"
	"helm.sh/helm/v3/pkg/action"
	"helm.sh/helm/v3/pkg/chart/loader"
	"helm.sh/helm/v3/pkg/chartutil"
)

var (
	KUBERNETES_VERSIONS = []string{
		"1.22.0",
		"1.23.0",
		"1.24.0",
		"1.25.0",
		"1.26.0",
		"1.27.0",
		"1.28.0",
	}
)

func TestKubeconform(t *testing.T) {
	t.Parallel()

	files, err := os.ReadDir("./")
	require.NoError(t, err)
	require.NotEmpty(t, files)

	schemas := []string{
		"https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/{{ .NormalizedKubernetesVersion }}-standalone{{ .StrictSuffix }}/{{ .ResourceKind }}{{ .KindSuffix }}.json",
		"https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json",
	}

	var clients map[string]*action.Install = make(map[string]*action.Install)
	for _, version := range KUBERNETES_VERSIONS {
		kubeVersion, err := chartutil.ParseKubeVersion(version)
		require.NoError(t, err)

		client := action.NewInstall(&action.Configuration{})
		client.ClientOnly = true
		client.DryRun = true
		client.ReleaseName = "kubeconform"
		client.Namespace = "default"
		client.IncludeCRDs = true
		client.KubeVersion = kubeVersion

		clients[version] = client
	}

	var validators map[string]validator.Validator = make(map[string]validator.Validator)
	for _, version := range KUBERNETES_VERSIONS {
		opts := validator.Opts{
			KubernetesVersion: version,
			SkipKinds: map[string]struct{}{
				"CephBlockPool":   {},
				"CephCluster":     {},
				"CephFilesystem":  {},
				"CephObjectStore": {},
				"apiextensions.k8s.io/v1/CustomResourceDefinition": {},
			},
			Strict: true,
		}

		v, err := validator.New(schemas, opts)
		require.NoError(t, err)

		validators[version] = v
	}

	for _, file := range files {
		if !file.IsDir() {
			continue
		}

		t.Run(file.Name(), func(t *testing.T) {
			chart, err := loader.LoadDir(file.Name())
			require.NoError(t, err)

			t.Parallel()

			for _, version := range KUBERNETES_VERSIONS {
				t.Run(version, func(t *testing.T) {
					client := clients[version]
					v := validators[version]

					t.Parallel()

					rel, err := client.Run(chart, map[string]interface{}{})
					require.NoError(t, err)

					manifests := io.NopCloser(strings.NewReader(rel.Manifest))
					for _, res := range v.Validate(chart.Name(), manifests) {
						require.NoError(t, res.Err)
						assert.Empty(t, res.ValidationErrors)
					}
				})
			}
		})
	}
}
