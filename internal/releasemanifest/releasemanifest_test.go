package releasemanifest

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/goccy/go-yaml"
	"github.com/opencontainers/go-digest"
	"github.com/opencontainers/image-spec/specs-go"
	ocispec "github.com/opencontainers/image-spec/specs-go/v1"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"oras.land/oras-go/v2"
	"oras.land/oras-go/v2/content"
	"oras.land/oras-go/v2/content/memory"
)

const (
	digestA = "sha256:1b9158ce28975f95def6a0ad459fa19f1336506074267a4b47c1bd914a00fec0"
	digestB = "sha256:3095eaa3964b6b37b55d9de8681fb3d06cc247da1cd402fcdf81a7abbfc2496b"
)

func testManifest() *Manifest {
	return &Manifest{
		APIVersion: APIVersion,
		Kind:       Kind,
		Release:    "main",
		Commit:     "811b7f90",
		Kubernetes: Kubernetes{
			Version: "1.28.13",
			Images:  []string{"kube_apiserver", "kube_controller_manager", "kube_proxy", "kube_scheduler"},
		},
		Images: map[string]string{
			"ceph":                    "quay.io/ceph/ceph:v18.2.7@" + digestA,
			"nova_api":                "ghcr.io/vexxhost/nova:main@" + digestB,
			"nova_conductor":          "ghcr.io/vexxhost/nova:main@" + digestB,
			"kube_apiserver":          "registry.k8s.io/kube-apiserver:v1.28.13@" + digestA,
			"kube_controller_manager": "registry.k8s.io/kube-controller-manager:v1.28.13@" + digestA,
			"kube_proxy":              "registry.k8s.io/kube-proxy:v1.28.13@" + digestA,
			"kube_scheduler":          "registry.k8s.io/kube-scheduler:v1.28.13@" + digestA,
		},
	}
}

func TestParseReference(t *testing.T) {
	ref, err := ParseReference("localhost:5000/a/b:v1@" + digestA)
	require.NoError(t, err)
	assert.Equal(t, "localhost:5000/a/b", ref.Repository)
	assert.Equal(t, "localhost:5000", ref.Registry())
	assert.Equal(t, "a/b", ref.Path())
	assert.Equal(t, "v1", ref.Tag)
	assert.Equal(t, digestA, ref.Digest)
	assert.Equal(t, "localhost:5000/a/b@"+digestA, ref.Pullable())

	for _, invalid := range []string{
		"haproxy:2.5",
		"library/haproxy:2.5",
		"quay.io/ceph/ceph",
		"quay.io/Ceph/ceph:v1",
		"quay.io/ceph/ceph@sha256:abc",
	} {
		_, err := ParseReference(invalid)
		assert.Error(t, err, invalid)
	}
}

func TestManifestRoundTripIsDeterministic(t *testing.T) {
	m := testManifest()

	first, err := m.Marshal()
	require.NoError(t, err)
	second, err := m.Marshal()
	require.NoError(t, err)
	assert.Equal(t, first, second)
	assert.True(t, strings.HasPrefix(string(first), "apiVersion: "+APIVersion+"\nkind: "+Kind+"\n"))

	parsed, err := Unmarshal(first)
	require.NoError(t, err)
	assert.Equal(t, m, parsed)
}

func TestManifestValidate(t *testing.T) {
	m := testManifest()
	m.Images["ceph"] = "quay.io/ceph/ceph:v18.2.7"
	assert.ErrorContains(t, m.Validate(), "not pinned by digest")

	m = testManifest()
	m.Kubernetes.Images = append(m.Kubernetes.Images, "missing")
	assert.ErrorContains(t, m.Validate(), "not part of the manifest images")

	m = testManifest()
	m.APIVersion = "v0"
	assert.ErrorContains(t, m.Validate(), "unsupported apiVersion")
}

type fakeResolver map[string]digest.Digest

func (f fakeResolver) Resolve(_ context.Context, reference string) (digest.Digest, error) {
	if d, ok := f[reference]; ok {
		return d, nil
	}
	return "", fmt.Errorf("not found")
}

const testVars = `---
# comment kept by write-vars
atmosphere_release: main
ceph_version: 18.2.7

_atmosphere_images:
  ceph: "{{ atmosphere_image_prefix }}quay.io/ceph/ceph:v{{ ceph_version }}"
  glance: "{{ atmosphere_image_prefix }}registry.atmosphere.dev/library/glance:{{ atmosphere_release }}"
  nova_api: "{{ atmosphere_image_prefix }}ghcr.io/vexxhost/nova:main@` + digestB + `"
  kube_apiserver: "{{ atmosphere_image_prefix }}registry.k8s.io/kube-apiserver:v{{ atmosphere_kubernetes_version }}"

atmosphere_images: '{{ _atmosphere_images }}'
`

const testDefaults = `---
atmosphere_image_prefix: ""
atmosphere_kubernetes_version: "1.28.13"
`

func writeSource(t *testing.T) (string, string) {
	t.Helper()
	dir := t.TempDir()
	vars := filepath.Join(dir, "vars.yml")
	defaults := filepath.Join(dir, "defaults.yml")
	require.NoError(t, os.WriteFile(vars, []byte(testVars), 0o644))
	require.NoError(t, os.WriteFile(defaults, []byte(testDefaults), 0o644))
	return vars, defaults
}

func TestGenerate(t *testing.T) {
	vars, defaults := writeSource(t)

	src, err := LoadSource(vars, defaults)
	require.NoError(t, err)
	assert.Equal(t, "main", src.Release)
	assert.Equal(t, "1.28.13", src.KubernetesVersion)
	assert.Equal(t, []string{"kube_apiserver"}, src.KubernetesImages)
	assert.Equal(t, "quay.io/ceph/ceph:v18.2.7", src.Images["ceph"])
	assert.Equal(t, "registry.atmosphere.dev/library/glance:main", src.Images["glance"])

	resolver := fakeResolver{
		"quay.io/ceph/ceph:v18.2.7":                   digestA,
		"registry.atmosphere.dev/library/glance:main": digestA,
		"registry.k8s.io/kube-apiserver:v1.28.13":     digestB,
	}
	m, err := Generate(context.Background(), src, resolver, GenerateOptions{Commit: "abc"})
	require.NoError(t, err)
	assert.Equal(t, "abc", m.Commit)
	assert.Equal(t, "quay.io/ceph/ceph:v18.2.7@"+digestA, m.Images["ceph"])
	// Existing digest pins are kept without resolving them again.
	assert.Equal(t, "ghcr.io/vexxhost/nova:main@"+digestB, m.Images["nova_api"])
	assert.Equal(t, "registry.k8s.io/kube-apiserver:v1.28.13@"+digestB, m.Images["kube_apiserver"])

	delete(resolver, "quay.io/ceph/ceph:v18.2.7")
	_, err = Generate(context.Background(), src, resolver, GenerateOptions{})
	assert.ErrorContains(t, err, "quay.io/ceph/ceph:v18.2.7")
}

func TestLoadSourceRejectsUnknownTemplate(t *testing.T) {
	vars, defaults := writeSource(t)
	data, err := os.ReadFile(vars)
	require.NoError(t, err)
	require.NoError(t, os.WriteFile(vars, []byte(strings.Replace(string(data), "ceph_version }}", "unknown }}", 1)), 0o644))

	_, err = LoadSource(vars, defaults)
	assert.ErrorContains(t, err, "undefined template variables")
}

func TestWriteVars(t *testing.T) {
	vars, defaults := writeSource(t)
	src, err := LoadSource(vars, defaults)
	require.NoError(t, err)

	m := &Manifest{
		APIVersion: APIVersion,
		Kind:       Kind,
		Release:    "main",
		Kubernetes: Kubernetes{Version: "1.28.13", Images: []string{"kube_apiserver"}},
		Images: map[string]string{
			"ceph":           "quay.io/ceph/ceph:v18.2.7@" + digestA,
			"glance":         "registry.atmosphere.dev/library/glance:main@" + digestA,
			"nova_api":       "ghcr.io/vexxhost/nova:main@" + digestA,
			"kube_apiserver": "registry.k8s.io/kube-apiserver:v1.28.13@" + digestB,
		},
	}
	require.NoError(t, WriteVars(vars, m))

	data, err := os.ReadFile(vars)
	require.NoError(t, err)
	assert.Contains(t, string(data), "# comment kept by write-vars")

	var parsed map[string]interface{}
	require.NoError(t, yaml.Unmarshal(data, &parsed))
	images := parsed["_atmosphere_images"].(map[string]interface{})
	assert.Equal(t, "{{ atmosphere_image_prefix }}quay.io/ceph/ceph:v18.2.7@"+digestA, images["ceph"])
	assert.Equal(t, "{{ atmosphere_image_prefix }}ghcr.io/vexxhost/nova:main@"+digestA, images["nova_api"])
	assert.Equal(t, "{{ atmosphere_image_prefix }}registry.k8s.io/kube-apiserver:v{{ atmosphere_kubernetes_version }}", images["kube_apiserver"])
	assert.Equal(t, "{{ _atmosphere_images }}", parsed["atmosphere_images"])

	// The rewritten file still renders to the manifest images.
	again, err := LoadSource(vars, defaults)
	require.NoError(t, err)
	assert.Equal(t, m.Images["ceph"], again.Images["ceph"])
	assert.Equal(t, src.KubernetesImages, again.KubernetesImages)

	delete(m.Images, "glance")
	assert.ErrorContains(t, WriteVars(vars, m), `image "glance" is missing`)
}

func TestDiff(t *testing.T) {
	a := testManifest()
	b := testManifest()
	b.Images["nova_api"] = "ghcr.io/vexxhost/nova:main@" + digestA
	b.Images["nova_conductor"] = "ghcr.io/vexxhost/nova:main@" + digestA
	delete(b.Images, "ceph")

	changes := Diff(a, b)
	require.Len(t, changes, 2)
	assert.Equal(t, []string{"ceph"}, changes[0].Keys)
	assert.Equal(t, "", changes[0].To)
	assert.Equal(t, []string{"nova_api", "nova_conductor"}, changes[1].Keys)

	var out bytes.Buffer
	require.NoError(t, WriteDiff(&out, a, b, changes))
	assert.Contains(t, out.String(), "keys: nova_api, nova_conductor")
	assert.Empty(t, Diff(a, a))
}

// registry is a set of in-memory repositories.
type registry map[string]*memory.Store

func (r registry) factory(repository string) (oras.Target, error) {
	if _, ok := r[repository]; !ok {
		r[repository] = memory.New()
	}
	return r[repository], nil
}

func pushJSON(t *testing.T, store *memory.Store, mediaType string, v interface{}) ocispec.Descriptor {
	t.Helper()
	data, err := json.Marshal(v)
	require.NoError(t, err)
	desc := content.NewDescriptorFromBytes(mediaType, data)
	exists, err := store.Exists(context.Background(), desc)
	require.NoError(t, err)
	if !exists {
		require.NoError(t, store.Push(context.Background(), desc, bytes.NewReader(data)))
	}
	return desc
}

// pushImage pushes a two-platform image and tags it with tag and its digest.
func pushImage(t *testing.T, store *memory.Store, tag string) string {
	t.Helper()
	ctx := context.Background()

	var manifests []ocispec.Descriptor
	for _, arch := range []string{"amd64", "arm64"} {
		config := pushJSON(t, store, ocispec.MediaTypeImageConfig, map[string]string{"architecture": arch, "os": "linux", "tag": tag})
		layer := pushJSON(t, store, ocispec.MediaTypeImageLayer, map[string]string{"layer": arch + tag})
		m := pushJSON(t, store, ocispec.MediaTypeImageManifest, ocispec.Manifest{
			Versioned: specs.Versioned{SchemaVersion: 2},
			MediaType: ocispec.MediaTypeImageManifest,
			Config:    config,
			Layers:    []ocispec.Descriptor{layer},
		})
		m.Platform = &ocispec.Platform{Architecture: arch, OS: "linux"}
		manifests = append(manifests, m)
	}
	index := pushJSON(t, store, ocispec.MediaTypeImageIndex, ocispec.Index{
		Versioned: specs.Versioned{SchemaVersion: 2},
		MediaType: ocispec.MediaTypeImageIndex,
		Manifests: manifests,
	})
	require.NoError(t, store.Tag(ctx, index, tag))
	require.NoError(t, store.Tag(ctx, index, index.Digest.String()))
	return index.Digest.String()
}

// sourceRegistry builds a source registry and a manifest pointing at it.
func sourceRegistry(t *testing.T) (registry, *Manifest) {
	t.Helper()
	src := registry{}
	m := testManifest()
	for key, value := range m.Images {
		ref, err := ParseReference(value)
		require.NoError(t, err)
		target, _ := src.factory(ref.Repository)
		ref.Digest = pushImage(t, target.(*memory.Store), ref.Tag)
		m.Images[key] = ref.String()
	}
	return src, m
}

func TestPushFetchPromote(t *testing.T) {
	ctx := context.Background()
	repo := memory.New()
	m := testManifest()

	desc, err := Push(ctx, repo, m, []string{"abc", "main"}, PushOptions{Source: "https://github.com/vexxhost/atmosphere"})
	require.NoError(t, err)

	got, fetched, err := Fetch(ctx, repo, "main")
	require.NoError(t, err)
	assert.Equal(t, m, got)
	assert.Equal(t, desc.Digest, fetched.Digest)

	promoted, err := Promote(ctx, repo, "abc", "v7.8.1")
	require.NoError(t, err)
	assert.Equal(t, desc.Digest, promoted.Digest)

	_, err = Promote(ctx, repo, "missing", "v7.8.2")
	assert.Error(t, err)

	reg := registry{DefaultManifestRepository: repo}
	loaded, err := Load(ctx, DefaultManifestRepository+":v7.8.1", reg.factory)
	require.NoError(t, err)
	assert.Equal(t, m, loaded)

	file := filepath.Join(t.TempDir(), FileName)
	data, err := m.Marshal()
	require.NoError(t, err)
	require.NoError(t, os.WriteFile(file, data, 0o644))
	loaded, err = Load(ctx, file, reg.factory)
	require.NoError(t, err)
	assert.Equal(t, m, loaded)
}

func TestFetchRejectsOtherArtifacts(t *testing.T) {
	ctx := context.Background()
	repo := memory.New()
	pushImage(t, repo, "image")
	_, _, err := Fetch(ctx, repo, "image")
	assert.Error(t, err)
}

func TestMirrorLayouts(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		layout     Layout
		kubePrefix string
		ceph       string
		kube       string
		manifest   string
	}{
		{LayoutNested, "", "mirror.example.com/atmosphere/quay.io/ceph/ceph", "mirror.example.com/atmosphere/registry.k8s.io/kube-apiserver", "mirror.example.com/atmosphere/ghcr.io/vexxhost/atmosphere-release:v7.8.1"},
		{LayoutFlat, "", "mirror.example.com/atmosphere/quay.io--ceph--ceph", "mirror.example.com/atmosphere/kube-apiserver", "mirror.example.com/atmosphere/ghcr.io--vexxhost--atmosphere-release:v7.8.1"},
		{LayoutSingleRepository, "mirror.example.com/kubernetes", "mirror.example.com/atmosphere", "mirror.example.com/kubernetes/kube-apiserver", "mirror.example.com/atmosphere:ghcr.io--vexxhost--atmosphere-release--v7.8.1"},
	}

	for _, tc := range tests {
		t.Run(string(tc.layout), func(t *testing.T) {
			src, m := sourceRegistry(t)
			manifestRepo := memory.New()
			_, err := Push(ctx, manifestRepo, m, []string{"v7.8.1"}, PushOptions{})
			require.NoError(t, err)
			src[DefaultManifestRepository] = manifestRepo

			plan, err := PlanMirror(m, MirrorOptions{
				Destination:      "mirror.example.com/atmosphere",
				Layout:           tc.layout,
				KubernetesPrefix: tc.kubePrefix,
				ManifestSource:   DefaultManifestRepository + ":v7.8.1",
			})
			require.NoError(t, err)
			assert.Equal(t, tc.manifest, plan.ManifestReference())

			dst := registry{}
			require.NoError(t, Mirror(ctx, m, plan, RemoteSource(src.factory), RemoteSource(src.factory), dst.factory, nil))

			resolved, err := ResolveImages(m.Images, ResolveOptions{Mirrors: plan.Rules})
			require.NoError(t, err)
			assert.True(t, strings.HasPrefix(resolved["ceph"], tc.ceph+":"), resolved["ceph"])
			assert.True(t, strings.HasPrefix(resolved["kube_apiserver"], tc.kube+":v1.28.13@"), resolved["kube_apiserver"])
			assert.Empty(t, CheckResolved(m, resolved))

			// Every resolved image points at a mirrored repository that holds
			// the image with an unchanged digest.
			items := map[string]MirrorItem{}
			for _, item := range plan.Items {
				items[item.Source.String()] = item
			}
			for key, value := range resolved {
				ref, err := ParseReference(value)
				require.NoError(t, err)
				item, ok := items[m.Images[key]]
				require.True(t, ok, key)
				assert.Equal(t, item.Repository, ref.Repository, key)
				store, ok := dst[ref.Repository]
				require.True(t, ok, "%s: repository %s not mirrored", key, ref.Repository)
				desc, err := store.Resolve(ctx, item.Tags[0])
				require.NoError(t, err)
				assert.Equal(t, ref.Digest, desc.Digest.String(), key)
			}

			// kubeadm pulls the control plane images by tag.
			kube, err := ParseReference(resolved["kube_apiserver"])
			require.NoError(t, err)
			_, err = dst[kube.Repository].Resolve(ctx, kube.Tag)
			assert.NoError(t, err)

			// The release manifest keeps its artifact digest.
			mirroredManifest, _, err := splitTarget(plan.ManifestReference())
			require.NoError(t, err)
			original, err := manifestRepo.Resolve(ctx, "v7.8.1")
			require.NoError(t, err)
			copied, err := dst[mirroredManifest].Resolve(ctx, plan.Manifest.Tags[0])
			require.NoError(t, err)
			assert.Equal(t, original.Digest, copied.Digest)
		})
	}
}

func TestPlanMirrorRegistryWithPort(t *testing.T) {
	m := testManifest()
	m.Images["local"] = "localhost:5000/team/tool:v1@" + digestA

	for layout, expected := range map[Layout][2]string{
		LayoutNested: {"mirror.example.com/localhost-5000/team/tool", "mirror.example.com/localhost-5000/vexxhost/atmosphere-release:v1"},
		LayoutFlat:   {"mirror.example.com/localhost-5000--team--tool", "mirror.example.com/localhost-5000--vexxhost--atmosphere-release:v1"},
	} {
		plan, err := PlanMirror(m, MirrorOptions{
			Destination:    "mirror.example.com",
			Layout:         layout,
			ManifestSource: "localhost:5000/vexxhost/atmosphere-release:v1",
		})
		require.NoError(t, err, layout)
		resolved, err := ResolveImages(m.Images, ResolveOptions{Mirrors: plan.Rules})
		require.NoError(t, err)
		assert.Equal(t, expected[0]+":v1@"+digestA, resolved["local"], layout)
		assert.Equal(t, expected[1], plan.ManifestReference(), layout)
	}
}

func TestPlanMirrorRequiresKubernetesPrefixForSingleRepository(t *testing.T) {
	_, err := PlanMirror(testManifest(), MirrorOptions{Destination: "mirror.example.com/atmosphere", Layout: LayoutSingleRepository})
	assert.ErrorContains(t, err, "--kubernetes-prefix")
}

func TestMirrorDetectsDigestMismatch(t *testing.T) {
	ctx := context.Background()
	src, m := sourceRegistry(t)
	ref, err := ParseReference(m.Images["ceph"])
	require.NoError(t, err)

	// Make the source serve different content for the pinned digest, as a
	// broken or tampered registry would.
	store := src[ref.Repository]
	pushImage(t, store, "other")
	other, err := store.Resolve(ctx, "other")
	require.NoError(t, err)
	require.NoError(t, store.Tag(ctx, other, ref.Digest))

	plan, err := PlanMirror(m, MirrorOptions{Destination: "mirror.example.com/atmosphere", Layout: LayoutNested})
	require.NoError(t, err)

	dst := registry{}
	err = Mirror(ctx, m, plan, RemoteSource(src.factory), nil, dst.factory, nil)
	assert.ErrorContains(t, err, "digest mismatch")
}

func TestExportImport(t *testing.T) {
	ctx := context.Background()
	src, m := sourceRegistry(t)
	manifestRepo := memory.New()
	_, err := Push(ctx, manifestRepo, m, []string{"v7.8.1"}, PushOptions{})
	require.NoError(t, err)
	src[DefaultManifestRepository] = manifestRepo

	extraStore, _ := src.factory("registry.k8s.io/etcd")
	pushImage(t, extraStore.(*memory.Store), "3.5.15-0")

	opts := MirrorOptions{
		ManifestSource: DefaultManifestRepository + ":v7.8.1",
		ExtraImages:    []string{"registry.k8s.io/etcd:3.5.15-0"},
	}
	dir := t.TempDir()
	require.NoError(t, Export(ctx, m, opts, RemoteSource(src.factory), RemoteSource(src.factory), dir, nil))
	assert.FileExists(t, filepath.Join(dir, FileName))
	assert.FileExists(t, filepath.Join(dir, "index.json"))

	dst := registry{}
	plan, err := Import(ctx, dir, MirrorOptions{Destination: "registry.internal/atmosphere", Layout: LayoutFlat}, dst.factory, nil)
	require.NoError(t, err)
	assert.Equal(t, "registry.internal/atmosphere/ghcr.io--vexxhost--atmosphere-release:v7.8.1", plan.ManifestReference())

	_, err = dst["registry.internal/atmosphere/etcd"].Resolve(ctx, "3.5.15-0")
	assert.NoError(t, err, "extra kubeadm image is mirrored next to the control plane images")

	mirrored, err := Load(ctx, plan.ManifestReference(), dst.factory)
	require.NoError(t, err)
	assert.Equal(t, m, mirrored)
}

type flakyResolver struct {
	failures int
	err      error
	calls    int
}

func (f *flakyResolver) Resolve(_ context.Context, _ string) (digest.Digest, error) {
	f.calls++
	if f.calls <= f.failures {
		return "", f.err
	}
	return digestA, nil
}

func TestGenerateRetriesRateLimits(t *testing.T) {
	src := &Source{Release: "main", Images: map[string]string{"ceph": "quay.io/ceph/ceph:v18.2.7"}}

	flaky := &flakyResolver{failures: 2, err: fmt.Errorf("toomanyrequests: rate limit")}
	m, err := Generate(context.Background(), src, flaky, GenerateOptions{Attempts: 3, Backoff: time.Millisecond})
	require.NoError(t, err)
	assert.Equal(t, 3, flaky.calls)
	assert.Equal(t, "quay.io/ceph/ceph:v18.2.7@"+digestA, m.Images["ceph"])

	permanent := &flakyResolver{failures: 10, err: fmt.Errorf("manifest unknown")}
	_, err = Generate(context.Background(), src, permanent, GenerateOptions{Attempts: 3, Backoff: time.Millisecond})
	assert.ErrorContains(t, err, "manifest unknown")
	assert.Equal(t, 1, permanent.calls, "permanent errors are not retried")
}

func TestSplitReferences(t *testing.T) {
	repo, tags, err := SplitReferences([]string{
		"ghcr.io/vexxhost/atmosphere-release:4f2c1ab0\nghcr.io/vexxhost/atmosphere-release:stable-2025.2\n",
		"",
	})
	require.NoError(t, err)
	assert.Equal(t, "ghcr.io/vexxhost/atmosphere-release", repo)
	assert.Equal(t, []string{"4f2c1ab0", "stable-2025.2"}, tags)

	_, _, err = SplitReferences([]string{"ghcr.io/a/b:x", "ghcr.io/a/c:y"})
	assert.ErrorContains(t, err, "one repository")

	_, _, err = SplitReferences([]string{"ghcr.io/a/b@" + digestA})
	assert.ErrorContains(t, err, "not a digest")

	_, _, err = SplitReferences([]string{" "})
	assert.Error(t, err)

	_, _, err = SplitReferences([]string{"localhost:5000/a/b"})
	assert.Error(t, err)
}

type prefixResolver struct {
	digests map[string]digest.Digest
	calls   []string
}

func (p *prefixResolver) Resolve(_ context.Context, reference string) (digest.Digest, error) {
	p.calls = append(p.calls, reference)
	if d, ok := p.digests[reference]; ok {
		return d, nil
	}
	return "", fmt.Errorf("manifest unknown")
}

func TestGenerateResolvePrefix(t *testing.T) {
	src := &Source{Release: "main", Images: map[string]string{
		"haproxy":  "docker.io/library/haproxy:2.5",
		"smartctl": "packages.vexxhost.com/smartctl-exporter:0.14.0-1",
	}}
	resolver := &prefixResolver{digests: map[string]digest.Digest{
		"harbor.example.com/docker.io/library/haproxy:2.5": digestA,
		"packages.vexxhost.com/smartctl-exporter:0.14.0-1": digestB,
	}}

	m, err := Generate(context.Background(), src, resolver, GenerateOptions{ResolvePrefix: "harbor.example.com/", Attempts: 1})
	require.NoError(t, err)
	// The manifest records the original references.
	assert.Equal(t, "docker.io/library/haproxy:2.5@"+digestA, m.Images["haproxy"])
	// Tags the cache cannot resolve fall back to the source registry.
	assert.Equal(t, "packages.vexxhost.com/smartctl-exporter:0.14.0-1@"+digestB, m.Images["smartctl"])
	assert.NotContains(t, resolver.calls, "docker.io/library/haproxy:2.5")
}

func openAppend(path string) (*os.File, error) {
	return os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0o644)
}
