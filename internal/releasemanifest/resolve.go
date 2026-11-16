package releasemanifest

import (
	"fmt"
	"path"
	"sort"
	"strings"
)

// MirrorRule redirects images from a source location to a mirror location.
//
// Source is a registry host ("quay.io"), a namespace ("quay.io/ceph") or a
// single repository ("quay.io/ceph/ceph"). The part of an image repository
// matching Source is replaced by Mirror; the remainder of the path, the tag
// and the digest are kept. When several rules match, the most specific
// (longest) Source wins.
type MirrorRule struct {
	Source string `yaml:"source" json:"source"`
	Mirror string `yaml:"mirror" json:"mirror"`
}

// Validate checks a mirror rule.
func (r MirrorRule) Validate() error {
	for name, value := range map[string]string{"source": r.Source, "mirror": r.Mirror} {
		if value == "" {
			return fmt.Errorf("mirror rule %s must not be empty", name)
		}
		if strings.HasSuffix(value, "/") || strings.ContainsAny(value, "@ ") {
			return fmt.Errorf("mirror rule %s %q must be a registry, namespace or repository without a tag or digest", name, value)
		}
		last := value[strings.LastIndex(value, "/")+1:]
		if strings.Contains(last, ":") && strings.Contains(value, "/") {
			return fmt.Errorf("mirror rule %s %q must not contain a tag", name, value)
		}
	}
	return nil
}

func (r MirrorRule) matches(repository string) bool {
	return repository == r.Source || strings.HasPrefix(repository, r.Source+"/")
}

// ResolveOptions controls how image references are resolved for deployment.
type ResolveOptions struct {
	// Prefix is atmosphere_image_prefix. It applies to images that no mirror
	// rule matches.
	Prefix string
	// Mirrors are the atmosphere_image_mirrors rules.
	Mirrors []MirrorRule
	// StripPrefix is set when the input comes from the source vars file,
	// where values already carry the prefix. The prefix is removed before
	// matching rules, and values that no rule matches are returned
	// unchanged, exactly as they were before mirror rules existed.
	StripPrefix bool
}

// ResolveImage returns the reference to deploy for a canonical image.
func ResolveImage(value string, opts ResolveOptions) (string, error) {
	if opts.StripPrefix && len(opts.Mirrors) == 0 {
		return value, nil
	}

	canonical := value
	if opts.StripPrefix {
		canonical = strings.TrimPrefix(canonical, opts.Prefix)
	}

	ref, err := ParseReference(canonical)
	if err != nil {
		return "", err
	}

	var best *MirrorRule
	for i := range opts.Mirrors {
		rule := opts.Mirrors[i]
		if err := rule.Validate(); err != nil {
			return "", err
		}
		if rule.matches(ref.Repository) && (best == nil || len(rule.Source) > len(best.Source)) {
			best = &opts.Mirrors[i]
		}
	}

	if best == nil {
		if opts.StripPrefix {
			return value, nil
		}
		return opts.Prefix + canonical, nil
	}

	ref.Repository = best.Mirror + strings.TrimPrefix(ref.Repository, best.Source)
	return ref.String(), nil
}

// ResolveImages resolves every image in a map.
func ResolveImages(images map[string]string, opts ResolveOptions) (map[string]string, error) {
	out := make(map[string]string, len(images))
	for key, value := range images {
		resolved, err := ResolveImage(value, opts)
		if err != nil {
			return nil, fmt.Errorf("image %q: %w", key, err)
		}
		out[key] = resolved
	}
	return out, nil
}

// kubeadmImages are the images kubeadm pulls by tag from its single image
// repository setting. They must stay together, under their original names,
// wherever they are mirrored.
var kubeadmImages = map[string]bool{
	"kube-apiserver":          true,
	"kube-controller-manager": true,
	"kube-scheduler":          true,
	"kube-proxy":              true,
	"etcd":                    true,
	"pause":                   true,
	"coredns/coredns":         true,
}

// CheckResolved validates resolved references for a manifest: every value
// must parse, and the Kubernetes control plane images must share one image
// repository and keep their original names, because kubeadm derives every
// control plane image from a single repository.
func CheckResolved(m *Manifest, resolved map[string]string) []error {
	var errs []error

	keys := make([]string, 0, len(resolved))
	for key := range resolved {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		if _, err := ParseReference(resolved[key]); err != nil {
			errs = append(errs, fmt.Errorf("image %q resolves to an invalid reference: %w", key, err))
		}
	}

	parents := map[string][]string{}
	for _, key := range m.Kubernetes.Images {
		original, err := ParseReference(m.Images[key])
		if err != nil {
			continue
		}
		ref, err := ParseReference(resolved[key])
		if err != nil {
			continue
		}
		if path.Base(ref.Repository) != path.Base(original.Repository) {
			errs = append(errs, fmt.Errorf("kubernetes image %q must keep its name %q, got %q", key, path.Base(original.Repository), ref.Repository))
			continue
		}
		dir := path.Dir(ref.Repository)
		parents[dir] = append(parents[dir], key)
	}
	if len(parents) > 1 {
		dirs := make([]string, 0, len(parents))
		for dir, keys := range parents {
			dirs = append(dirs, fmt.Sprintf("%s (%s)", dir, strings.Join(keys, ", ")))
		}
		sort.Strings(dirs)
		errs = append(errs, fmt.Errorf("kubernetes images must share one image repository, got: %s", strings.Join(dirs, "; ")))
	}

	return errs
}
