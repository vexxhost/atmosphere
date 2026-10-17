package releasemanifest

import (
	"fmt"
	"os"
	"strings"

	"github.com/goccy/go-yaml"
	"github.com/goccy/go-yaml/ast"
	"github.com/goccy/go-yaml/parser"
)

// WriteVars rewrites the image list in the defaults role vars file so that
// every image is the digest-pinned reference from the manifest, keeping the
// "{{ atmosphere_image_prefix }}" template in front of each value.
//
// Images whose tag follows the Kubernetes version are left untouched so that
// operators can still deploy a different Kubernetes version.
func WriteVars(varsPath string, m *Manifest) error {
	file, err := parser.ParseFile(varsPath, parser.ParseComments)
	if err != nil {
		return fmt.Errorf("parsing %s: %w", varsPath, err)
	}
	if len(file.Docs) != 1 {
		return fmt.Errorf("expected exactly one YAML document in %s", varsPath)
	}

	body, ok := file.Docs[0].Body.(*ast.MappingNode)
	if !ok {
		return fmt.Errorf("expected a mapping at the top of %s", varsPath)
	}

	var images *ast.MappingNode
	for _, item := range body.Values {
		key, ok := item.Key.(*ast.StringNode)
		if ok && key.Value == imagesKey {
			images, _ = item.Value.(*ast.MappingNode)
		}
	}
	if images == nil {
		return fmt.Errorf("%s not found in %s", imagesKey, varsPath)
	}

	seen := map[string]bool{}
	for _, item := range images.Values {
		key := item.Key.(*ast.StringNode).Value
		value, ok := item.Value.(*ast.StringNode)
		if !ok {
			return fmt.Errorf("image %q in %s is not a string", key, varsPath)
		}
		seen[key] = true

		if strings.Contains(value.Value, kubernetesVariable) {
			continue
		}

		pinned, ok := m.Images[key]
		if !ok {
			return fmt.Errorf("image %q is missing from the release manifest", key)
		}

		node, err := yaml.ValueToNode("{{ " + prefixVariable + " }}" + pinned)
		if err != nil {
			return fmt.Errorf("image %q: %w", key, err)
		}
		item.Value = node
	}

	for key := range m.Images {
		if !seen[key] {
			return fmt.Errorf("release manifest image %q is not defined in %s", key, varsPath)
		}
	}

	return os.WriteFile(varsPath, []byte(file.String()), 0o644)
}
