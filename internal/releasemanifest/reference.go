package releasemanifest

import (
	"fmt"
	"regexp"
	"strings"
)

var (
	// pathComponent follows the OCI distribution specification.
	pathComponent = regexp.MustCompile(`^[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*$`)
	tagPattern    = regexp.MustCompile(`^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$`)
	digestPattern = regexp.MustCompile(`^sha256:[a-f0-9]{64}$`)
)

// Reference is a fully qualified image reference split into its parts.
type Reference struct {
	// Repository includes the registry host, e.g. "quay.io/ceph/ceph".
	Repository string
	Tag        string
	Digest     string
}

// ParseReference parses a fully qualified image reference of the form
// host/path[:tag][@digest].
func ParseReference(value string) (Reference, error) {
	var ref Reference

	rest := value
	if i := strings.Index(rest, "@"); i >= 0 {
		ref.Digest = rest[i+1:]
		rest = rest[:i]
		if !digestPattern.MatchString(ref.Digest) {
			return Reference{}, fmt.Errorf("invalid digest in %q", value)
		}
	}

	lastSlash := strings.LastIndex(rest, "/")
	if i := strings.LastIndex(rest, ":"); i > lastSlash {
		ref.Tag = rest[i+1:]
		rest = rest[:i]
		if !tagPattern.MatchString(ref.Tag) {
			return Reference{}, fmt.Errorf("invalid tag in %q", value)
		}
	}

	if lastSlash < 0 {
		return Reference{}, fmt.Errorf("image %q is not fully qualified (missing registry)", value)
	}

	ref.Repository = rest
	host := ref.Registry()
	if host != "localhost" && !strings.ContainsAny(host, ".:") {
		return Reference{}, fmt.Errorf("image %q is not fully qualified (missing registry)", value)
	}
	for _, component := range strings.Split(ref.Path(), "/") {
		if !pathComponent.MatchString(component) {
			return Reference{}, fmt.Errorf("invalid repository path component %q in %q", component, value)
		}
	}

	if ref.Tag == "" && ref.Digest == "" {
		return Reference{}, fmt.Errorf("image %q has neither a tag nor a digest", value)
	}

	return ref, nil
}

// Registry returns the registry host of the reference.
func (r Reference) Registry() string {
	return strings.SplitN(r.Repository, "/", 2)[0]
}

// Path returns the repository path without the registry host.
func (r Reference) Path() string {
	parts := strings.SplitN(r.Repository, "/", 2)
	if len(parts) < 2 {
		return ""
	}
	return parts[1]
}

// String returns the reference in host/path[:tag][@digest] form.
func (r Reference) String() string {
	s := r.Repository
	if r.Tag != "" {
		s += ":" + r.Tag
	}
	if r.Digest != "" {
		s += "@" + r.Digest
	}
	return s
}

// Pullable returns the reference used to pull the image: the digest when
// present, otherwise the tag.
func (r Reference) Pullable() string {
	if r.Digest != "" {
		return r.Repository + "@" + r.Digest
	}
	return r.Repository + ":" + r.Tag
}
