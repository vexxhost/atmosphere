package main

import (
	"context"
	"fmt"
	"os"
	"strings"
	"sync"

	"github.com/containers/image/v5/docker"
	"github.com/containers/image/v5/manifest"
	"github.com/containers/image/v5/types"
	"github.com/goccy/go-yaml"
	"github.com/goccy/go-yaml/ast"
	"github.com/goccy/go-yaml/parser"
	"github.com/opencontainers/go-digest"
	log "github.com/sirupsen/logrus"
	"golang.org/x/sync/singleflight"
)

var digestGroup singleflight.Group

// GetImageDigest fetches the digest for a given image reference.
func GetImageDigest(ctx context.Context, reference string) (digest.Digest, error) {
	ref, err := docker.ParseReference(reference)
	if err != nil {
		return "", fmt.Errorf("error parsing reference '%s': %w", reference, err)
	}

	sysCtx := &types.SystemContext{}
	imageSource, err := ref.NewImageSource(ctx, sysCtx)
	if err != nil {
		return "", fmt.Errorf("error creating image source for '%s': %w", reference, err)
	}
	defer imageSource.Close()

	rawManifest, _, err := imageSource.GetManifest(ctx, nil)
	if err != nil {
		return "", fmt.Errorf("error getting manifest for '%s': %w", reference, err)
	}

	dgst, err := manifest.Digest(rawManifest)
	if err != nil {
		return "", fmt.Errorf("error getting digest for '%s': %w", reference, err)
	}

	return dgst, nil
}

// GetImageNameToPull normalizes the image name by replacing variables and adding necessary prefixes.
func GetImageNameToPull(image string, release string) string {
	// Replace Jinja2 variables with actual values
	image = strings.ReplaceAll(image, "{{ atmosphere_image_prefix }}", "")
	image = strings.ReplaceAll(image, "{{ atmosphere_release }}", release)

	return image
}

// AppendDigestToImage appends the digest to the original image reference.
func AppendDigestToImage(image string, dgst digest.Digest) string {
	if strings.Contains(image, "@") {
		// Replace existing digest if present
		parts := strings.Split(image, "@")
		return parts[0] + "@" + dgst.String()
	}
	// Append digest
	return image + "@" + dgst.String()
}

func main() {
	varsFilePath := "roles/defaults/vars/main.yml"

	file, err := parser.ParseFile(varsFilePath, parser.ParseComments)
	if err != nil {
		log.WithError(err).Fatal("error parsing yaml file")
	}

	if len(file.Docs) != 1 {
		log.Fatal("expected exactly one yaml document")
	}

	doc := file.Docs[0]
	body := doc.Body.(*ast.MappingNode)

	var release string
	var images *ast.MappingNode

	for _, item := range body.Values {
		switch item.Key.(*ast.StringNode).Value {
		case "atmosphere_release":
			release = item.Value.(*ast.StringNode).Value
		case "_atmosphere_images":
			images = item.Value.(*ast.MappingNode)
		}
	}

	if release == "" {
		log.Fatalf("atmosphere_release not found")
	}

	if images == nil {
		log.Fatalf("_atmosphere_images not found")
	}

	type imageInfo struct {
		Key        string
		Value      string
		Normalized string
		Digest     digest.Digest
	}

	var imageInfos []imageInfo
	uniqueImages := make(map[string][]int)

	for i, item := range images.Values {
		normalized := GetImageNameToPull(item.Value.(*ast.StringNode).Value, release)
		info := imageInfo{
			Key:        item.Key.(*ast.StringNode).Value,
			Value:      item.Value.(*ast.StringNode).Value,
			Normalized: normalized,
		}
		imageInfos = append(imageInfos, info)
		uniqueImages[normalized] = append(uniqueImages[normalized], i)
	}

	digestMap := make(map[string]digest.Digest)
	var mapMutex sync.Mutex
	var wg sync.WaitGroup

	for normImg := range uniqueImages {
		wg.Add(1)
		go func(normImg string) {
			defer wg.Done()

			result, err, _ := digestGroup.Do(normImg, func() (interface{}, error) {
				dgst, err := GetImageDigest(context.TODO(), "//"+normImg)
				if err != nil {
					return nil, err
				}
				return dgst, nil
			})

			if err != nil {
				log.WithError(err).WithFields(log.Fields{
					"image": normImg,
				}).Error("Error fetching digest")
				return
			}

			dgst := result.(digest.Digest)

			mapMutex.Lock()
			digestMap[normImg] = dgst
			mapMutex.Unlock()

			log.WithFields(log.Fields{
				"image":  normImg,
				"digest": dgst,
			}).Info("Fetched image digest")
		}(normImg)
	}

	wg.Wait()

	// Update the image references with digests
	for normImg, indices := range uniqueImages {
		dgst, exists := digestMap[normImg]
		if !exists {
			log.WithField("image", normImg).Error("Digest not found, skipping update")
			continue
		}
		for _, idx := range indices {
			updatedImage, err := yaml.ValueToNode(AppendDigestToImage(imageInfos[idx].Value, dgst))
			if err != nil {
				log.WithError(err).Fatal("error converting value to node")
			}

			images.Values[idx].Value = updatedImage
		}
	}

	if err := os.WriteFile(varsFilePath, []byte(file.String()), 0644); err != nil {
		log.WithError(err).Fatal("error writing updated yaml file")
	}

	log.Info("Successfully updated YAML file with image digests")
}
