package releasemanifest

import (
	"fmt"
	"io"
	"sort"
	"strings"
)

// Change is one image that differs between two manifests, with every
// manifest key that uses it.
type Change struct {
	From string
	To   string
	Keys []string
}

// Diff returns the image changes between two manifests, grouped by
// (from, to) pair so an image shared by many keys is reported once.
func Diff(a, b *Manifest) []Change {
	grouped := map[[2]string][]string{}

	keys := map[string]struct{}{}
	for key := range a.Images {
		keys[key] = struct{}{}
	}
	for key := range b.Images {
		keys[key] = struct{}{}
	}

	for key := range keys {
		from, to := a.Images[key], b.Images[key]
		if from == to {
			continue
		}
		pair := [2]string{from, to}
		grouped[pair] = append(grouped[pair], key)
	}

	changes := make([]Change, 0, len(grouped))
	for pair, keys := range grouped {
		sort.Strings(keys)
		changes = append(changes, Change{From: pair[0], To: pair[1], Keys: keys})
	}
	sort.Slice(changes, func(i, j int) bool {
		return changes[i].Keys[0] < changes[j].Keys[0]
	})
	return changes
}

// WriteDiff prints changes in a human readable form.
func WriteDiff(w io.Writer, a, b *Manifest, changes []Change) error {
	if a.Kubernetes.Version != b.Kubernetes.Version {
		if _, err := fmt.Fprintf(w, "kubernetes: %s -> %s\n", a.Kubernetes.Version, b.Kubernetes.Version); err != nil {
			return err
		}
	}
	if len(changes) == 0 {
		_, err := fmt.Fprintln(w, "no image changes")
		return err
	}

	for _, change := range changes {
		var line string
		switch {
		case change.From == "":
			line = fmt.Sprintf("+ %s", change.To)
		case change.To == "":
			line = fmt.Sprintf("- %s", change.From)
		default:
			line = fmt.Sprintf("~ %s\n    -> %s", change.From, change.To)
		}
		if _, err := fmt.Fprintf(w, "%s\n    keys: %s\n", line, strings.Join(change.Keys, ", ")); err != nil {
			return err
		}
	}
	return nil
}
