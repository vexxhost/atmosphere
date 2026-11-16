// Package releasemanifest builds, publishes, mirrors and resolves Atmosphere
// release manifests: immutable, digest-pinned lists of every image that a
// given Atmosphere commit or release deploys.
package releasemanifest

import (
	"fmt"
	"sort"

	"github.com/goccy/go-yaml"
)

const (
	// APIVersion is the schema version of the release manifest document.
	APIVersion = "atmosphere.vexxhost.com/v1alpha1"

	// Kind is the kind of the release manifest document.
	Kind = "ReleaseManifest"

	// ArtifactType is the OCI artifact type used when publishing a manifest.
	ArtifactType = "application/vnd.vexxhost.atmosphere.release.v1"

	// MediaType is the media type of the layer holding the manifest document.
	MediaType = "application/vnd.vexxhost.atmosphere.release.v1+yaml"

	// FileName is the conventional file name of a release manifest.
	FileName = "release-manifest.yaml"
)

// Kubernetes describes the Kubernetes control plane images in a manifest.
//
// kubeadm pulls these images by tag from a single image repository, and
// operators may deploy a different Kubernetes version than the default one.
// Consumers use this information to fall back to the tag for the requested
// version when it differs from Version.
type Kubernetes struct {
	Version string   `yaml:"version"`
	Images  []string `yaml:"images"`
}

// Manifest is an Atmosphere release manifest.
type Manifest struct {
	APIVersion string `yaml:"apiVersion"`
	Kind       string `yaml:"kind"`
	Release    string `yaml:"release"`
	Commit     string `yaml:"commit,omitempty"`
	// Inputs is a digest of the image list the manifest was generated from
	// (see Source.Digest). Two manifests with the same Inputs were generated
	// from identical image definitions, even at different commits.
	Inputs     string            `yaml:"inputs,omitempty"`
	Kubernetes Kubernetes        `yaml:"kubernetes"`
	Images     map[string]string `yaml:"images"`
}

// Validate checks that the manifest is well formed and that every image is
// fully qualified and pinned by digest.
func (m *Manifest) Validate() error {
	if m.APIVersion != APIVersion {
		return fmt.Errorf("unsupported apiVersion %q (expected %q)", m.APIVersion, APIVersion)
	}
	if m.Kind != Kind {
		return fmt.Errorf("unsupported kind %q (expected %q)", m.Kind, Kind)
	}
	if len(m.Images) == 0 {
		return fmt.Errorf("manifest contains no images")
	}

	for key, value := range m.Images {
		ref, err := ParseReference(value)
		if err != nil {
			return fmt.Errorf("image %q: %w", key, err)
		}
		if ref.Digest == "" {
			return fmt.Errorf("image %q (%s) is not pinned by digest", key, value)
		}
	}

	for _, key := range m.Kubernetes.Images {
		if _, ok := m.Images[key]; !ok {
			return fmt.Errorf("kubernetes image %q is not part of the manifest images", key)
		}
	}

	return nil
}

// Marshal serializes the manifest deterministically: fields in a fixed order
// and map keys sorted, so identical content always produces identical bytes.
func (m *Manifest) Marshal() ([]byte, error) {
	if err := m.Validate(); err != nil {
		return nil, err
	}

	kubernetesImages := append([]string(nil), m.Kubernetes.Images...)
	sort.Strings(kubernetesImages)

	keys := make([]string, 0, len(m.Images))
	for key := range m.Images {
		keys = append(keys, key)
	}
	sort.Strings(keys)

	images := make(yaml.MapSlice, 0, len(keys))
	for _, key := range keys {
		images = append(images, yaml.MapItem{Key: key, Value: m.Images[key]})
	}

	doc := yaml.MapSlice{
		{Key: "apiVersion", Value: m.APIVersion},
		{Key: "kind", Value: m.Kind},
		{Key: "release", Value: m.Release},
	}
	if m.Commit != "" {
		doc = append(doc, yaml.MapItem{Key: "commit", Value: m.Commit})
	}
	if m.Inputs != "" {
		doc = append(doc, yaml.MapItem{Key: "inputs", Value: m.Inputs})
	}
	doc = append(doc,
		yaml.MapItem{Key: "kubernetes", Value: yaml.MapSlice{
			{Key: "version", Value: m.Kubernetes.Version},
			{Key: "images", Value: kubernetesImages},
		}},
		yaml.MapItem{Key: "images", Value: images},
	)

	return yaml.MarshalWithOptions(doc, yaml.IndentSequence(true))
}

// Unmarshal parses and validates a manifest document.
func Unmarshal(data []byte) (*Manifest, error) {
	var m Manifest
	if err := yaml.Unmarshal(data, &m); err != nil {
		return nil, fmt.Errorf("parsing release manifest: %w", err)
	}
	if err := m.Validate(); err != nil {
		return nil, fmt.Errorf("invalid release manifest: %w", err)
	}
	return &m, nil
}
