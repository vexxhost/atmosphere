package releasemanifest

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/containers/image/v5/docker"
	"github.com/containers/image/v5/manifest"
	"github.com/containers/image/v5/types"
	"github.com/goccy/go-yaml"
	"github.com/opencontainers/go-digest"
	"golang.org/x/sync/errgroup"
)

const (
	imagesKey            = "_atmosphere_images"
	prefixVariable       = "atmosphere_image_prefix"
	releaseVariable      = "atmosphere_release"
	kubernetesVariable   = "atmosphere_kubernetes_version"
	defaultResolverLimit = 16
)

var templateVariable = regexp.MustCompile(`\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}`)

// Resolver resolves an image tag to the digest it currently points to.
type Resolver interface {
	Resolve(ctx context.Context, reference string) (digest.Digest, error)
}

// Source describes the image list of an Atmosphere checkout.
type Source struct {
	Release           string
	KubernetesVersion string
	// Images holds the rendered, fully qualified image references without
	// the image prefix.
	Images map[string]string
	// KubernetesImages lists the image keys whose tag follows the
	// Kubernetes version.
	KubernetesImages []string
}

// LoadSource reads the defaults role vars and defaults files and renders the
// image list. Template variables are substituted from scalar values defined
// in either file; the image prefix is removed.
func LoadSource(varsPath, defaultsPath string) (*Source, error) {
	vars, images, err := readImageVars(varsPath)
	if err != nil {
		return nil, err
	}

	defaults := map[string]interface{}{}
	defaultsData, err := os.ReadFile(defaultsPath)
	if err != nil {
		return nil, fmt.Errorf("reading %s: %w", defaultsPath, err)
	}
	if err := yaml.Unmarshal(defaultsData, &defaults); err != nil {
		return nil, fmt.Errorf("parsing %s: %w", defaultsPath, err)
	}

	values := map[string]string{prefixVariable: ""}
	for _, source := range []map[string]interface{}{defaults, vars} {
		for key, value := range source {
			switch v := value.(type) {
			case string:
				values[key] = v
			case int, int64, uint64, float64, bool:
				values[key] = fmt.Sprint(v)
			}
		}
	}

	src := &Source{
		Release:           values[releaseVariable],
		KubernetesVersion: values[kubernetesVariable],
		Images:            map[string]string{},
	}

	for key, raw := range images {
		rendered, err := render(raw, values)
		if err != nil {
			return nil, fmt.Errorf("image %q: %w", key, err)
		}
		if _, err := ParseReference(rendered); err != nil {
			return nil, fmt.Errorf("image %q: %w", key, err)
		}
		src.Images[key] = rendered

		if strings.Contains(raw, kubernetesVariable) {
			src.KubernetesImages = append(src.KubernetesImages, key)
		}
	}
	sort.Strings(src.KubernetesImages)

	return src, nil
}

// Digest returns a digest of everything that determines the images of a
// release: the release, the Kubernetes version and images, and the rendered
// image references before any tag is resolved. Unrelated changes to the
// defaults role, such as the Atmosphere version, do not change it.
func (s *Source) Digest() string {
	data, err := json.Marshal(struct {
		Release           string            `json:"release"`
		KubernetesVersion string            `json:"kubernetesVersion"`
		KubernetesImages  []string          `json:"kubernetesImages"`
		Images            map[string]string `json:"images"`
	}{s.Release, s.KubernetesVersion, s.KubernetesImages, s.Images})
	if err != nil {
		panic(err) // only strings, cannot fail
	}
	sum := sha256.Sum256(data)
	return "sha256:" + hex.EncodeToString(sum[:])
}

func readImageVars(varsPath string) (map[string]interface{}, map[string]string, error) {
	data, err := os.ReadFile(varsPath)
	if err != nil {
		return nil, nil, fmt.Errorf("reading %s: %w", varsPath, err)
	}

	vars := map[string]interface{}{}
	if err := yaml.Unmarshal(data, &vars); err != nil {
		return nil, nil, fmt.Errorf("parsing %s: %w", varsPath, err)
	}

	raw, ok := vars[imagesKey].(map[string]interface{})
	if !ok {
		return nil, nil, fmt.Errorf("%s not found in %s", imagesKey, varsPath)
	}

	images := make(map[string]string, len(raw))
	for key, value := range raw {
		s, ok := value.(string)
		if !ok {
			return nil, nil, fmt.Errorf("image %q in %s is not a string", key, varsPath)
		}
		images[key] = s
	}

	return vars, images, nil
}

func render(raw string, values map[string]string) (string, error) {
	var missing []string
	rendered := templateVariable.ReplaceAllStringFunc(raw, func(match string) string {
		name := templateVariable.FindStringSubmatch(match)[1]
		value, ok := values[name]
		if !ok {
			missing = append(missing, name)
			return match
		}
		return value
	})
	if len(missing) > 0 {
		return "", fmt.Errorf("undefined template variables %v in %q", missing, raw)
	}
	return rendered, nil
}

// GenerateOptions controls manifest generation.
type GenerateOptions struct {
	Commit      string
	Concurrency int
	// Attempts is how many times a tag is resolved before giving up on
	// rate limits and transient network errors (default 5).
	Attempts int
	// Backoff is the delay before the first retry; it doubles after each
	// attempt (default 5s).
	Backoff time.Duration
	// ResolvePrefix resolves tags through a pull-through cache first, such as
	// "harbor.example.com/" in front of the original reference, to avoid
	// upstream rate limits. The manifest still records the original
	// references, and resolution falls back to the source registry when the
	// cache cannot resolve a tag.
	ResolvePrefix string
}

var retryable = []string{"toomanyrequests", "429", "timeout", "connection reset", "EOF", "502", "503", "504"}

func isRetryable(err error) bool {
	msg := err.Error()
	for _, s := range retryable {
		if strings.Contains(msg, s) {
			return true
		}
	}
	return false
}

func resolveWithRetry(ctx context.Context, resolver Resolver, reference string, attempts int, backoff time.Duration) (digest.Digest, error) {
	var err error
	for attempt := 1; ; attempt++ {
		var dgst digest.Digest
		dgst, err = resolver.Resolve(ctx, reference)
		if err == nil || attempt >= attempts || !isRetryable(err) {
			return dgst, err
		}
		select {
		case <-ctx.Done():
			return "", ctx.Err()
		case <-time.After(backoff):
		}
		backoff *= 2
	}
}

// Generate builds a release manifest from a rendered source. Images that are
// already pinned by digest keep their digest; images referenced by tag only
// are resolved to the digest the tag currently points to.
func Generate(ctx context.Context, src *Source, resolver Resolver, opts GenerateOptions) (*Manifest, error) {
	refs := make(map[string]Reference, len(src.Images))
	toResolve := map[string]struct{}{}
	for key, value := range src.Images {
		ref, err := ParseReference(value)
		if err != nil {
			return nil, fmt.Errorf("image %q: %w", key, err)
		}
		refs[key] = ref
		if ref.Digest == "" {
			toResolve[ref.Repository+":"+ref.Tag] = struct{}{}
		}
	}

	limit := opts.Concurrency
	if limit <= 0 {
		limit = defaultResolverLimit
	}
	attempts := opts.Attempts
	if attempts <= 0 {
		attempts = 5
	}
	backoff := opts.Backoff
	if backoff <= 0 {
		backoff = 5 * time.Second
	}

	var (
		mu       sync.Mutex
		resolved = map[string]digest.Digest{}
		failures []string
	)
	g, gctx := errgroup.WithContext(ctx)
	g.SetLimit(limit)
	for tagged := range toResolve {
		g.Go(func() error {
			var (
				dgst digest.Digest
				err  error
			)
			if opts.ResolvePrefix != "" {
				dgst, err = resolveWithRetry(gctx, resolver, opts.ResolvePrefix+tagged, attempts, backoff)
			}
			if opts.ResolvePrefix == "" || err != nil {
				dgst, err = resolveWithRetry(gctx, resolver, tagged, attempts, backoff)
			}
			mu.Lock()
			defer mu.Unlock()
			if err != nil {
				failures = append(failures, fmt.Sprintf("%s: %v", tagged, err))
				return nil
			}
			resolved[tagged] = dgst
			return nil
		})
	}
	if err := g.Wait(); err != nil {
		return nil, err
	}
	if len(failures) > 0 {
		sort.Strings(failures)
		return nil, fmt.Errorf("failed to resolve %d image(s):\n  %s", len(failures), strings.Join(failures, "\n  "))
	}

	m := &Manifest{
		APIVersion: APIVersion,
		Kind:       Kind,
		Release:    src.Release,
		Commit:     opts.Commit,
		Inputs:     src.Digest(),
		Kubernetes: Kubernetes{
			Version: src.KubernetesVersion,
			Images:  append([]string(nil), src.KubernetesImages...),
		},
		Images: make(map[string]string, len(refs)),
	}
	for key, ref := range refs {
		if ref.Digest == "" {
			ref.Digest = resolved[ref.Repository+":"+ref.Tag].String()
		}
		m.Images[key] = ref.String()
	}

	return m, m.Validate()
}

// DockerResolver resolves tags using the containers/image docker transport,
// honouring the usual registry authentication and configuration files.
type DockerResolver struct {
	SystemContext *types.SystemContext
}

// Resolve returns the digest of the manifest (or manifest list) for a tag.
func (r DockerResolver) Resolve(ctx context.Context, reference string) (digest.Digest, error) {
	ref, err := docker.ParseReference("//" + reference)
	if err != nil {
		return "", fmt.Errorf("parsing reference: %w", err)
	}

	sysCtx := r.SystemContext
	if sysCtx == nil {
		sysCtx = &types.SystemContext{}
	}

	src, err := ref.NewImageSource(ctx, sysCtx)
	if err != nil {
		return "", err
	}
	defer src.Close()

	raw, _, err := src.GetManifest(ctx, nil)
	if err != nil {
		return "", err
	}

	return manifest.Digest(raw)
}
