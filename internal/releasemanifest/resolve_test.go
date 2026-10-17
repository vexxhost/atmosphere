package releasemanifest

import (
	"os"
	"testing"

	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type resolveCase struct {
	Name        string       `yaml:"name"`
	Prefix      string       `yaml:"prefix"`
	StripPrefix bool         `yaml:"strip_prefix"`
	Mirrors     []MirrorRule `yaml:"mirrors"`
	Input       string       `yaml:"input"`
	Expected    string       `yaml:"expected"`
	Error       bool         `yaml:"error"`
}

func TestResolveImageSharedCases(t *testing.T) {
	data, err := os.ReadFile("testdata/resolve.yaml")
	require.NoError(t, err)

	var fixture struct {
		Cases []resolveCase `yaml:"cases"`
	}
	require.NoError(t, yaml.Unmarshal(data, &fixture))
	require.NotEmpty(t, fixture.Cases)

	for _, tc := range fixture.Cases {
		t.Run(tc.Name, func(t *testing.T) {
			got, err := ResolveImage(tc.Input, ResolveOptions{
				Prefix:      tc.Prefix,
				Mirrors:     tc.Mirrors,
				StripPrefix: tc.StripPrefix,
			})
			if tc.Error {
				assert.Error(t, err)
				return
			}
			require.NoError(t, err)
			assert.Equal(t, tc.Expected, got)
		})
	}
}

func TestCheckResolvedKubernetesImages(t *testing.T) {
	m := testManifest()

	resolved, err := ResolveImages(m.Images, ResolveOptions{Prefix: "harbor.example.com/"})
	require.NoError(t, err)
	assert.Empty(t, CheckResolved(m, resolved))

	resolved, err = ResolveImages(m.Images, ResolveOptions{Mirrors: []MirrorRule{
		{Source: "registry.k8s.io/kube-apiserver", Mirror: "registry.internal/flat--kube-apiserver"},
	}})
	require.NoError(t, err)
	errs := CheckResolved(m, resolved)
	require.Len(t, errs, 1)
	assert.Contains(t, errs[0].Error(), "must keep its name")

	resolved, err = ResolveImages(m.Images, ResolveOptions{Mirrors: []MirrorRule{
		{Source: "registry.k8s.io/kube-apiserver", Mirror: "registry.internal/a/kube-apiserver"},
	}})
	require.NoError(t, err)
	errs = CheckResolved(m, resolved)
	require.Len(t, errs, 1)
	assert.Contains(t, errs[0].Error(), "share one image repository")
}
