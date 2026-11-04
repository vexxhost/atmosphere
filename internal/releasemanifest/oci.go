package releasemanifest

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	ocispec "github.com/opencontainers/image-spec/specs-go/v1"
	"oras.land/oras-go/v2"
	"oras.land/oras-go/v2/content"
	"oras.land/oras-go/v2/content/memory"
	"oras.land/oras-go/v2/registry/remote"
	"oras.land/oras-go/v2/registry/remote/auth"
	"oras.land/oras-go/v2/registry/remote/credentials"
	"oras.land/oras-go/v2/registry/remote/retry"
)

const (
	annotationRevision = "org.opencontainers.image.revision"
	annotationSource   = "org.opencontainers.image.source"
	annotationTitle    = "org.opencontainers.image.title"
	annotationRelease  = "com.vexxhost.atmosphere.release"
)

// TargetFactory returns an OCI target for a repository.
type TargetFactory func(repository string) (oras.Target, error)

// RemoteOptions configures access to remote registries.
type RemoteOptions struct {
	// PlainHTTP uses HTTP instead of HTTPS (for local test registries).
	PlainHTTP bool
}

// NewRemoteFactory returns a TargetFactory for remote registries that uses
// the Docker credentials store (~/.docker/config.json and helpers).
func NewRemoteFactory(opts RemoteOptions) (TargetFactory, error) {
	store, err := credentials.NewStoreFromDocker(credentials.StoreOptions{})
	if err != nil {
		return nil, fmt.Errorf("loading docker credentials: %w", err)
	}

	client := &auth.Client{
		Client:     retry.DefaultClient,
		Cache:      auth.NewCache(),
		Credential: credentials.Credential(store),
	}

	return func(repository string) (oras.Target, error) {
		repo, err := remote.NewRepository(repository)
		if err != nil {
			return nil, err
		}
		// docker.io does not serve the registry API itself.
		if repo.Reference.Registry == "docker.io" {
			repo.Reference.Registry = "registry-1.docker.io"
		}
		repo.Client = client
		repo.PlainHTTP = opts.PlainHTTP
		return repo, nil
	}, nil
}

// splitTarget splits "repository:tag" or "repository@digest" into the
// repository and the reference within it.
func splitTarget(value string) (string, string, error) {
	if i := strings.Index(value, "@"); i >= 0 {
		return value[:i], value[i+1:], nil
	}
	lastSlash := strings.LastIndex(value, "/")
	if i := strings.LastIndex(value, ":"); i > lastSlash {
		return value[:i], value[i+1:], nil
	}
	return "", "", fmt.Errorf("%q must include a tag or digest", value)
}

// SplitReferences splits repository:tag references that must all point at
// the same repository, such as the tags output of docker/metadata-action.
// Surrounding whitespace and empty values are ignored.
func SplitReferences(references []string) (string, []string, error) {
	var repository string
	var tags []string
	for _, value := range references {
		for _, field := range strings.Fields(value) {
			repo, tag, err := splitTarget(field)
			if err != nil {
				return "", nil, err
			}
			if strings.HasPrefix(tag, "sha256:") {
				return "", nil, fmt.Errorf("%q must use a tag, not a digest", field)
			}
			if repository == "" {
				repository = repo
			} else if repo != repository {
				return "", nil, fmt.Errorf("all references must use one repository: %q and %q differ", repository, repo)
			}
			tags = append(tags, tag)
		}
	}
	if repository == "" {
		return "", nil, fmt.Errorf("at least one repository:tag reference is required")
	}
	return repository, tags, nil
}

// PushOptions controls publishing a manifest.
type PushOptions struct {
	Source string
	// Annotations are added to the artifact manifest.
	Annotations map[string]string
}

// createdEpoch is used as the creation time of every artifact, so that the
// same manifest always produces the same artifact digest.
const createdEpoch = "1970-01-01T00:00:00Z"

// pack builds the OCI artifact for a manifest in a memory store. The result
// is reproducible: identical manifests and options give identical digests.
func pack(ctx context.Context, m *Manifest, opts PushOptions) (*memory.Store, ocispec.Descriptor, error) {
	data, err := m.Marshal()
	if err != nil {
		return nil, ocispec.Descriptor{}, err
	}

	store := memory.New()
	layer := content.NewDescriptorFromBytes(MediaType, data)
	layer.Annotations = map[string]string{annotationTitle: FileName}
	if err := store.Push(ctx, layer, bytes.NewReader(data)); err != nil {
		return nil, ocispec.Descriptor{}, err
	}

	annotations := map[string]string{
		annotationRelease:         m.Release,
		ocispec.AnnotationCreated: createdEpoch,
	}
	if m.Commit != "" {
		annotations[annotationRevision] = m.Commit
	}
	if opts.Source != "" {
		annotations[annotationSource] = opts.Source
	}
	for key, value := range opts.Annotations {
		annotations[key] = value
	}

	desc, err := oras.PackManifest(ctx, store, oras.PackManifestVersion1_1, ArtifactType, oras.PackManifestOptions{
		Layers:              []ocispec.Descriptor{layer},
		ManifestAnnotations: annotations,
	})
	if err != nil {
		return nil, ocispec.Descriptor{}, err
	}
	return store, desc, nil
}

// Digest returns the digest of the artifact Push would publish for a
// manifest, without publishing it.
func Digest(ctx context.Context, m *Manifest, opts PushOptions) (string, error) {
	_, desc, err := pack(ctx, m, opts)
	if err != nil {
		return "", err
	}
	return desc.Digest.String(), nil
}

// Push publishes a manifest as an OCI artifact and tags it with every tag.
func Push(ctx context.Context, dst oras.Target, m *Manifest, tags []string, opts PushOptions) (ocispec.Descriptor, error) {
	if len(tags) == 0 {
		return ocispec.Descriptor{}, fmt.Errorf("at least one tag is required")
	}

	store, desc, err := pack(ctx, m, opts)
	if err != nil {
		return ocispec.Descriptor{}, err
	}

	if err := oras.CopyGraph(ctx, store, dst, desc, oras.DefaultCopyGraphOptions); err != nil {
		return ocispec.Descriptor{}, err
	}
	for _, tag := range tags {
		if err := dst.Tag(ctx, desc, tag); err != nil {
			return ocispec.Descriptor{}, err
		}
	}

	return desc, nil
}

// Fetch downloads and validates a manifest artifact.
func Fetch(ctx context.Context, src oras.ReadOnlyTarget, reference string) (*Manifest, ocispec.Descriptor, error) {
	desc, raw, err := oras.FetchBytes(ctx, src, reference, oras.DefaultFetchBytesOptions)
	if err != nil {
		return nil, ocispec.Descriptor{}, err
	}

	var artifact ocispec.Manifest
	if err := json.Unmarshal(raw, &artifact); err != nil {
		return nil, ocispec.Descriptor{}, fmt.Errorf("parsing artifact manifest: %w", err)
	}
	if artifact.ArtifactType != ArtifactType {
		return nil, ocispec.Descriptor{}, fmt.Errorf("%s is not an Atmosphere release manifest (artifact type %q)", reference, artifact.ArtifactType)
	}

	for _, layer := range artifact.Layers {
		if layer.MediaType != MediaType {
			continue
		}
		data, err := content.FetchAll(ctx, src, layer)
		if err != nil {
			return nil, ocispec.Descriptor{}, err
		}
		m, err := Unmarshal(data)
		if err != nil {
			return nil, ocispec.Descriptor{}, err
		}
		return m, desc, nil
	}

	return nil, ocispec.Descriptor{}, fmt.Errorf("%s does not contain a %s layer", reference, MediaType)
}

// Promote tags an existing manifest artifact with a new tag, without
// changing its content.
func Promote(ctx context.Context, repo oras.Target, from, to string) (ocispec.Descriptor, error) {
	if _, _, err := Fetch(ctx, repo, from); err != nil {
		return ocispec.Descriptor{}, err
	}
	return oras.Tag(ctx, repo, from, to)
}

// Load reads a manifest from a local file or, if no such file exists, from
// an OCI reference such as ghcr.io/vexxhost/atmosphere-release:v7.8.1.
func Load(ctx context.Context, location string, factory TargetFactory) (*Manifest, error) {
	if data, err := os.ReadFile(location); err == nil {
		return Unmarshal(data)
	} else if !os.IsNotExist(err) {
		return nil, err
	}

	repository, reference, err := splitTarget(location)
	if err != nil {
		return nil, fmt.Errorf("%s is neither a file nor an OCI reference: %w", location, err)
	}
	target, err := factory(repository)
	if err != nil {
		return nil, err
	}
	m, _, err := Fetch(ctx, target, reference)
	return m, err
}
