package releasemanifest

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/goccy/go-yaml"
	ocispec "github.com/opencontainers/image-spec/specs-go/v1"
	"oras.land/oras-go/v2"
	"oras.land/oras-go/v2/content/oci"
)

// Layout describes how images are named in a mirror registry.
type Layout string

const (
	// LayoutNested keeps the full source path under the destination:
	// quay.io/ceph/ceph -> <destination>/quay.io/ceph/ceph.
	LayoutNested Layout = "nested"
	// LayoutFlat encodes the full source path into one component:
	// quay.io/ceph/ceph -> <destination>/quay.io--ceph--ceph.
	LayoutFlat Layout = "flat"
	// LayoutSingleRepository stores every image in one repository and
	// encodes the source in the tag.
	LayoutSingleRepository Layout = "single-repo"

	// DefaultManifestRepository is where Atmosphere publishes manifests.
	DefaultManifestRepository = "ghcr.io/vexxhost/atmosphere-release"

	extraImagesFile = "extra-images.yaml"
	sourceFile      = "source.yaml"
	maxTagLength    = 128
)

var invalidTagCharacters = regexp.MustCompile(`[^a-zA-Z0-9._-]`)

// MirrorOptions controls how a release is mirrored.
type MirrorOptions struct {
	// Destination is a registry or namespace (nested and flat layouts) or a
	// repository (single-repo layout).
	Destination string
	Layout      Layout
	// KubernetesPrefix is the image repository kubeadm pulls the control
	// plane images from. It defaults to <destination>/registry.k8s.io for
	// the nested layout and <destination> for the flat layout, and must be
	// set for the single-repo layout.
	KubernetesPrefix string
	// ExtraImages are additional fully qualified images to mirror, such as
	// the etcd and CoreDNS images kubeadm uses for a Kubernetes version.
	ExtraImages []string
	// ManifestSource is the canonical location of the release manifest,
	// e.g. ghcr.io/vexxhost/atmosphere-release:v7.8.1.
	ManifestSource string
}

// MirrorItem is one image to copy.
type MirrorItem struct {
	Source     Reference
	Repository string
	Tags       []string
}

// MirrorPlan is the result of planning a mirror.
type MirrorPlan struct {
	Items []MirrorItem
	// Rules redirect every mirrored image to its mirror location; they are
	// the atmosphere_image_mirrors value for the mirrored deployment.
	Rules []MirrorRule
	// Manifest is where the release manifest itself is mirrored to.
	Manifest MirrorItem
}

// mirrorPath returns a source repository as a valid path inside a mirror;
// a port in the registry host ("localhost:5000") becomes "localhost-5000".
func mirrorPath(repository string) string {
	return strings.Replace(repository, ":", "-", 1)
}

func flatName(repository string) string {
	return strings.ReplaceAll(mirrorPath(repository), "/", "--")
}

func digestTag(dgst string) string {
	return strings.Replace(dgst, ":", "-", 1)
}

// uniqueTag builds a valid, collision-free tag from parts.
func uniqueTag(parts ...string) string {
	tag := invalidTagCharacters.ReplaceAllString(strings.Join(parts, "--"), "-")
	if len(tag) <= maxTagLength {
		return tag
	}
	sum := sha256.Sum256([]byte(strings.Join(parts, "--")))
	suffix := "--" + hex.EncodeToString(sum[:])[:16]
	return tag[:maxTagLength-len(suffix)] + suffix
}

func isKubeadmImage(ref Reference) bool {
	return ref.Registry() == "registry.k8s.io" && kubeadmImages[ref.Path()]
}

// PlanMirror computes destinations, tags and mirror rules for a manifest.
func PlanMirror(m *Manifest, opts MirrorOptions) (*MirrorPlan, error) {
	dest := strings.TrimSuffix(opts.Destination, "/")
	if dest == "" {
		return nil, fmt.Errorf("a destination is required")
	}

	kubePrefix := strings.TrimSuffix(opts.KubernetesPrefix, "/")
	natural := ""
	switch opts.Layout {
	case LayoutNested:
		natural = dest + "/registry.k8s.io"
	case LayoutFlat:
		natural = dest
	case LayoutSingleRepository:
		if kubePrefix == "" {
			return nil, fmt.Errorf("the %s layout needs --kubernetes-prefix: kubeadm pulls each control plane image from its own repository under one prefix", LayoutSingleRepository)
		}
	default:
		return nil, fmt.Errorf("unknown layout %q (expected %s, %s or %s)", opts.Layout, LayoutNested, LayoutFlat, LayoutSingleRepository)
	}
	if kubePrefix == "" {
		kubePrefix = natural
	}

	refs := map[string]Reference{}
	for key, value := range m.Images {
		ref, err := ParseReference(value)
		if err != nil {
			return nil, fmt.Errorf("image %q: %w", key, err)
		}
		refs[ref.String()] = ref
	}
	for _, value := range opts.ExtraImages {
		ref, err := ParseReference(value)
		if err != nil {
			return nil, fmt.Errorf("extra image: %w", err)
		}
		refs[ref.String()] = ref
	}

	plan := &MirrorPlan{}
	rules := map[string]string{}
	occupied := map[string]string{}

	addRule := func(source, mirror string) error {
		if existing, ok := rules[source]; ok && existing != mirror {
			return fmt.Errorf("conflicting mirror locations for %s: %s and %s", source, existing, mirror)
		}
		rules[source] = mirror
		return nil
	}

	keys := make([]string, 0, len(refs))
	for key := range refs {
		keys = append(keys, key)
	}
	sort.Strings(keys)

	for _, key := range keys {
		ref := refs[key]
		tag := ref.Tag
		if tag == "" {
			tag = digestTag(ref.Digest)
		}

		item := MirrorItem{Source: ref}
		switch {
		case isKubeadmImage(ref):
			item.Repository = kubePrefix + "/" + ref.Path()
			item.Tags = []string{tag}
			if opts.Layout == LayoutNested && kubePrefix == natural {
				if err := addRule(ref.Registry(), dest+"/"+mirrorPath(ref.Registry())); err != nil {
					return nil, err
				}
			} else if err := addRule(ref.Repository, item.Repository); err != nil {
				return nil, err
			}
		case opts.Layout == LayoutNested:
			item.Repository = dest + "/" + mirrorPath(ref.Repository)
			item.Tags = []string{tag}
			if err := addRule(ref.Registry(), dest+"/"+mirrorPath(ref.Registry())); err != nil {
				return nil, err
			}
		case opts.Layout == LayoutFlat:
			item.Repository = dest + "/" + flatName(ref.Repository)
			item.Tags = []string{tag}
			if err := addRule(ref.Repository, item.Repository); err != nil {
				return nil, err
			}
		default:
			item.Repository = dest
			item.Tags = []string{uniqueTag(flatName(ref.Repository), tag)}
			if err := addRule(ref.Repository, dest); err != nil {
				return nil, err
			}
		}

		for _, t := range item.Tags {
			location := item.Repository + ":" + t
			if previous, ok := occupied[location]; ok && previous != ref.String() {
				return nil, fmt.Errorf("%s and %s would both be mirrored to %s", previous, ref.String(), location)
			}
			occupied[location] = ref.String()
		}
		plan.Items = append(plan.Items, item)
	}

	sources := make([]string, 0, len(rules))
	for source := range rules {
		sources = append(sources, source)
	}
	sort.Strings(sources)
	for _, source := range sources {
		plan.Rules = append(plan.Rules, MirrorRule{Source: source, Mirror: rules[source]})
	}

	manifestSource := opts.ManifestSource
	if manifestSource == "" {
		manifestSource = DefaultManifestRepository + ":latest"
	}
	manifestRepository, manifestTag, err := splitTarget(manifestSource)
	if err != nil {
		return nil, err
	}
	if strings.HasPrefix(manifestTag, "sha256:") {
		manifestTag = digestTag(manifestTag)
	}
	plan.Manifest = MirrorItem{Source: Reference{Repository: manifestRepository, Tag: manifestTag}}
	switch opts.Layout {
	case LayoutNested:
		plan.Manifest.Repository = dest + "/" + mirrorPath(manifestRepository)
		plan.Manifest.Tags = []string{manifestTag}
	case LayoutFlat:
		plan.Manifest.Repository = dest + "/" + flatName(manifestRepository)
		plan.Manifest.Tags = []string{manifestTag}
	default:
		plan.Manifest.Repository = dest
		plan.Manifest.Tags = []string{uniqueTag(flatName(manifestRepository), manifestTag)}
	}

	// Validate that the rules resolve every image of the release in a way
	// that kubeadm can use.
	resolved, err := ResolveImages(m.Images, ResolveOptions{Mirrors: plan.Rules})
	if err != nil {
		return nil, err
	}
	if errs := CheckResolved(m, resolved); len(errs) > 0 {
		return nil, fmt.Errorf("mirror rules would not work: %v", errs)
	}

	return plan, nil
}

// ManifestReference returns the mirrored release manifest reference.
func (p *MirrorPlan) ManifestReference() string {
	return p.Manifest.Repository + ":" + p.Manifest.Tags[0]
}

// SourceFunc returns where to read an item from and the reference to read.
type SourceFunc func(item MirrorItem) (oras.ReadOnlyTarget, string, error)

// RemoteSource reads items from their source registries.
func RemoteSource(factory TargetFactory) SourceFunc {
	return func(item MirrorItem) (oras.ReadOnlyTarget, string, error) {
		target, err := factory(item.Source.Repository)
		if err != nil {
			return nil, "", err
		}
		return target, item.Source.Pullable()[len(item.Source.Repository)+1:], nil
	}
}

// Progress receives mirror progress messages.
type Progress func(format string, args ...interface{})

// copyItem copies a complete image (all platforms) and verifies its digest.
func copyItem(ctx context.Context, item MirrorItem, src SourceFunc, dst oras.Target, dstTag string) (ocispec.Descriptor, error) {
	srcTarget, srcRef, err := src(item)
	if err != nil {
		return ocispec.Descriptor{}, err
	}

	desc, err := oras.Copy(ctx, srcTarget, srcRef, dst, dstTag, oras.DefaultCopyOptions)
	if err != nil {
		return ocispec.Descriptor{}, fmt.Errorf("copying %s: %w", item.Source.String(), err)
	}
	if item.Source.Digest != "" && desc.Digest.String() != item.Source.Digest {
		return ocispec.Descriptor{}, fmt.Errorf("digest mismatch for %s: copied %s", item.Source.String(), desc.Digest)
	}

	got, err := dst.Resolve(ctx, dstTag)
	if err != nil {
		return ocispec.Descriptor{}, fmt.Errorf("verifying %s: %w", dstTag, err)
	}
	if got.Digest != desc.Digest {
		return ocispec.Descriptor{}, fmt.Errorf("digest mismatch after copying %s: destination has %s, expected %s", item.Source.String(), got.Digest, desc.Digest)
	}
	return desc, nil
}

// Mirror copies every image in the plan, then the release manifest itself.
// manifestSrc reads the release manifest artifact; when it is nil the
// manifest is published to the mirror from m instead, which gives it a new
// artifact digest but identical content.
func Mirror(ctx context.Context, m *Manifest, plan *MirrorPlan, src SourceFunc, manifestSrc SourceFunc, dst TargetFactory, progress Progress) error {
	if progress == nil {
		progress = func(string, ...interface{}) {}
	}

	for i, item := range plan.Items {
		target, err := dst(item.Repository)
		if err != nil {
			return err
		}
		desc, err := copyItem(ctx, item, src, target, item.Tags[0])
		if err != nil {
			return err
		}
		for _, tag := range item.Tags[1:] {
			if err := target.Tag(ctx, desc, tag); err != nil {
				return err
			}
		}
		progress("[%d/%d] %s -> %s:%s", i+1, len(plan.Items), item.Source.String(), item.Repository, item.Tags[0])
	}

	target, err := dst(plan.Manifest.Repository)
	if err != nil {
		return err
	}
	if manifestSrc != nil {
		if _, err := copyItem(ctx, plan.Manifest, manifestSrc, target, plan.Manifest.Tags[0]); err != nil {
			return err
		}
	} else if _, err := Push(ctx, target, m, plan.Manifest.Tags, PushOptions{}); err != nil {
		return err
	}
	progress("release manifest -> %s", plan.ManifestReference())

	return nil
}

// directoryKey is the tag used for an image inside an OCI layout directory.
func directoryKey(ref Reference) string {
	tag := ref.Tag
	if tag == "" {
		tag = "untagged"
	}
	digest := strings.TrimPrefix(ref.Digest, "sha256:")
	if len(digest) > 12 {
		digest = digest[:12]
	}
	return uniqueTag(flatName(ref.Repository), tag, digest)
}

type directorySource struct {
	Manifest string `yaml:"manifest"`
}

// Export copies a release, its manifest and extra images into an OCI image
// layout directory that can be carried into a disconnected environment.
func Export(ctx context.Context, m *Manifest, opts MirrorOptions, src SourceFunc, manifestSrc SourceFunc, dir string, progress Progress) error {
	if progress == nil {
		progress = func(string, ...interface{}) {}
	}

	// The layout of the final mirror is decided at import time; plan with a
	// placeholder destination to collect and validate the images.
	planOpts := opts
	planOpts.Destination = "export.invalid"
	planOpts.Layout = LayoutNested
	planOpts.KubernetesPrefix = ""
	plan, err := PlanMirror(m, planOpts)
	if err != nil {
		return err
	}

	store, err := oci.NewWithContext(ctx, dir)
	if err != nil {
		return err
	}

	for i, item := range plan.Items {
		if _, err := copyItem(ctx, item, src, store, directoryKey(item.Source)); err != nil {
			return err
		}
		progress("[%d/%d] %s", i+1, len(plan.Items), item.Source.String())
	}

	manifestKey := uniqueTag("release-manifest", plan.Manifest.Source.Tag)
	if manifestSrc != nil {
		if _, err := copyItem(ctx, plan.Manifest, manifestSrc, store, manifestKey); err != nil {
			return err
		}
	} else if _, err := Push(ctx, store, m, []string{manifestKey}, PushOptions{}); err != nil {
		return err
	}

	data, err := m.Marshal()
	if err != nil {
		return err
	}
	if err := os.WriteFile(filepath.Join(dir, FileName), data, 0o644); err != nil {
		return err
	}

	extra, err := yaml.Marshal(opts.ExtraImages)
	if err != nil {
		return err
	}
	if err := os.WriteFile(filepath.Join(dir, extraImagesFile), extra, 0o644); err != nil {
		return err
	}

	source := opts.ManifestSource
	if source == "" {
		source = DefaultManifestRepository + ":latest"
	}
	meta, err := yaml.Marshal(directorySource{Manifest: source})
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(dir, sourceFile), meta, 0o644)
}

// Import reads a directory written by Export and mirrors it to a registry.
func Import(ctx context.Context, dir string, opts MirrorOptions, dst TargetFactory, progress Progress) (*MirrorPlan, error) {
	data, err := os.ReadFile(filepath.Join(dir, FileName))
	if err != nil {
		return nil, err
	}
	m, err := Unmarshal(data)
	if err != nil {
		return nil, err
	}

	if raw, err := os.ReadFile(filepath.Join(dir, extraImagesFile)); err == nil {
		if err := yaml.Unmarshal(raw, &opts.ExtraImages); err != nil {
			return nil, err
		}
	}
	if raw, err := os.ReadFile(filepath.Join(dir, sourceFile)); err == nil {
		var meta directorySource
		if err := yaml.Unmarshal(raw, &meta); err != nil {
			return nil, err
		}
		opts.ManifestSource = meta.Manifest
	}

	plan, err := PlanMirror(m, opts)
	if err != nil {
		return nil, err
	}

	store, err := oci.NewWithContext(ctx, dir)
	if err != nil {
		return nil, err
	}
	src := func(item MirrorItem) (oras.ReadOnlyTarget, string, error) {
		return store, directoryKey(item.Source), nil
	}
	manifestSrc := func(item MirrorItem) (oras.ReadOnlyTarget, string, error) {
		return store, uniqueTag("release-manifest", item.Source.Tag), nil
	}

	if err := Mirror(ctx, m, plan, src, manifestSrc, dst, progress); err != nil {
		return nil, err
	}
	return plan, nil
}
