package releasemanifest

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type fakeZuul struct {
	server   *httptest.Server
	builds   map[string][]map[string]interface{} // pipeline -> builds
	results  map[string]string                   // buildset -> result
	manifest []byte
	queries  []string
}

func newFakeZuul(t *testing.T, manifest *Manifest) *fakeZuul {
	t.Helper()
	data, err := manifest.Marshal()
	require.NoError(t, err)
	z := &fakeZuul{builds: map[string][]map[string]interface{}{}, results: map[string]string{}, manifest: data}
	mux := http.NewServeMux()
	mux.HandleFunc("/api/builds", func(w http.ResponseWriter, r *http.Request) {
		z.queries = append(z.queries, r.URL.RawQuery)
		q := r.URL.Query()
		if q.Get("project") != "vexxhost/atmosphere" || q.Get("change") != "4420" || q.Get("patchset") != "abc" ||
			q.Get("job_name") != DefaultZuulJob || q.Get("result") != "SUCCESS" {
			_ = json.NewEncoder(w).Encode([]interface{}{})
			return
		}
		_ = json.NewEncoder(w).Encode(z.builds[q.Get("pipeline")])
	})
	mux.HandleFunc("/api/buildset/", func(w http.ResponseWriter, r *http.Request) {
		uuid := r.URL.Path[len("/api/buildset/"):]
		_ = json.NewEncoder(w).Encode(map[string]string{"result": z.results[uuid]})
	})
	mux.HandleFunc("/logs/release-manifest.yaml", func(w http.ResponseWriter, _ *http.Request) {
		_, _ = w.Write(z.manifest)
	})
	z.server = httptest.NewServer(mux)
	t.Cleanup(z.server.Close)
	return z
}

func (z *fakeZuul) addBuild(pipeline, buildset, result string) {
	z.results[buildset] = result
	z.builds[pipeline] = append(z.builds[pipeline], map[string]interface{}{
		"uuid":     "build-" + buildset,
		"result":   "SUCCESS",
		"buildset": map[string]string{"uuid": buildset},
		"artifacts": []map[string]string{
			{"name": "Zuul Manifest", "url": z.server.URL + "/logs/zuul-manifest.json"},
			{"name": DefaultZuulArtifact, "url": z.server.URL + "/logs/release-manifest.yaml"},
		},
	})
}

func (z *fakeZuul) lookup() *ZuulLookup {
	return &ZuulLookup{API: z.server.URL + "/api", Project: "vexxhost/atmosphere", Change: "4420", Patchset: "abc", Pipelines: []string{"gate", "check"}}
}

func TestDecidePublishUsesTestedManifest(t *testing.T) {
	ctx := context.Background()
	tested := testManifest()
	tested.Inputs = "sha256:inputs"
	z := newFakeZuul(t, tested)
	z.addBuild("check", "failed-buildset", "FAILURE")
	z.addBuild("check", "good-buildset", "SUCCESS")

	fallback := testManifest()
	fallback.Images["ceph"] = "quay.io/ceph/ceph:v18.2.7@" + digestB
	fallback.Inputs = "sha256:inputs"

	d, err := DecidePublish(ctx, z.lookup(), "sha256:inputs", fallback, PushOptions{Source: "src"})
	require.NoError(t, err)
	require.NotNil(t, d.Tested)
	assert.Equal(t, "good-buildset", d.Tested.Buildset)
	assert.Equal(t, "check", d.Tested.Pipeline)
	assert.Equal(t, tested, d.Manifest)
	assert.Empty(t, d.Options.Annotations)

	// Publishing the tested manifest gives the same artifact digest as the
	// one the producer job computed.
	want, err := Digest(ctx, tested, PushOptions{Source: "src"})
	require.NoError(t, err)
	got, err := Digest(ctx, d.Manifest, d.Options)
	require.NoError(t, err)
	assert.Equal(t, want, got)

	// gate is searched before check.
	assert.Contains(t, z.queries[0], "pipeline=gate")
}

func TestDecidePublishFallsBack(t *testing.T) {
	ctx := context.Background()
	tested := testManifest()
	tested.Inputs = "sha256:old"
	fallback := testManifest()

	cases := map[string]struct {
		setup  func(z *fakeZuul) *ZuulLookup
		inputs string
		reason string
	}{
		"inputs changed": {
			setup:  func(z *fakeZuul) *ZuulLookup { z.addBuild("check", "bs", "SUCCESS"); return z.lookup() },
			inputs: "sha256:new",
			reason: "image inputs changed",
		},
		"no successful buildset": {
			setup:  func(z *fakeZuul) *ZuulLookup { z.addBuild("check", "bs", "FAILURE"); return z.lookup() },
			inputs: "sha256:old",
			reason: "no successful buildset",
		},
		"no change": {
			setup:  func(*fakeZuul) *ZuulLookup { return nil },
			inputs: "sha256:old",
			reason: "no change",
		},
		"zuul unreachable": {
			setup: func(z *fakeZuul) *ZuulLookup {
				l := z.lookup()
				l.API = "http://127.0.0.1:1/api"
				return l
			},
			inputs: "sha256:old",
			reason: "looking up the tested manifest failed",
		},
	}

	for name, tc := range cases {
		t.Run(name, func(t *testing.T) {
			z := newFakeZuul(t, tested)
			d, err := DecidePublish(ctx, tc.setup(z), tc.inputs, fallback, PushOptions{})
			require.NoError(t, err)
			assert.Nil(t, d.Tested)
			assert.Equal(t, fallback, d.Manifest)
			assert.Contains(t, d.Reason, tc.reason)
			assert.Equal(t, "false", d.Options.Annotations[AnnotationTested])
		})
	}
}

func TestPushIsReproducible(t *testing.T) {
	ctx := context.Background()
	m := testManifest()
	a, err := Digest(ctx, m, PushOptions{Source: "s"})
	require.NoError(t, err)
	b, err := Digest(ctx, m, PushOptions{Source: "s"})
	require.NoError(t, err)
	assert.Equal(t, a, b)

	other := testManifest()
	other.Release = "2025.2"
	c, err := Digest(ctx, other, PushOptions{Source: "s"})
	require.NoError(t, err)
	assert.NotEqual(t, a, c)

	// Push and Digest agree.
	reg := registry{}
	repo, _ := reg.factory("example.com/release")
	desc, err := Push(ctx, repo, m, []string{"x"}, PushOptions{Source: "s"})
	require.NoError(t, err)
	assert.Equal(t, a, desc.Digest.String())
}

func TestSourceDigestIgnoresUnrelatedDefaults(t *testing.T) {
	vars, defaults := writeSource(t)
	a, err := LoadSource(vars, defaults)
	require.NoError(t, err)

	require.NoError(t, appendFile(defaults, "atmosphere_version: 9.9.9\n"))
	b, err := LoadSource(vars, defaults)
	require.NoError(t, err)
	assert.Equal(t, a.Digest(), b.Digest())

	b.Images["ceph"] = "quay.io/ceph/ceph:v19.0.0"
	assert.NotEqual(t, a.Digest(), b.Digest())
	assert.Regexp(t, `^sha256:[a-f0-9]{64}$`, a.Digest())
}

func appendFile(path, data string) error {
	f, err := openAppend(path)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = fmt.Fprint(f, data)
	return err
}
