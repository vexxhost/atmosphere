package defaults

import (
	"bytes"
	"context"
	"fmt"
	"slices"
	"strings"
	"testing"

	"github.com/containers/image/v5/docker"
	"github.com/goccy/go-yaml"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestImageHasPrefix(t *testing.T) {
	path, err := yaml.PathString("$._atmosphere_images")
	require.NoError(t, err)

	var images map[string]string
	err = path.Read(bytes.NewReader(varsFile), &images)
	require.NoError(t, err)

	prefix := "{{ atmosphere_image_prefix }}"

	for _, image := range images {
		testName := strings.ReplaceAll(image, prefix, "")

		t.Run(testName, func(t *testing.T) {
			assert.True(t, strings.HasPrefix(image, prefix))
		})
	}
}

func TestImageExist(t *testing.T) {
	images, err := GetImages()
	require.NoError(t, err)

	var uniqueImages []string
	for _, image := range images {
		if slices.Contains(uniqueImages, image) {
			continue
		}

		uniqueImages = append(uniqueImages, image)
	}

	for _, image := range uniqueImages {
		// NOTE(mnaser): ParseReference does not allow both tag & digest,
		//               so we strip the tags from the image name.
		nameWithTagSplit := strings.Split(image, "@")
		// NOTE(okozachenko1203): We'll enable this again when use image digest.
		// require.Len(t, nameWithTagSplit, 2)
		nameWithTag := nameWithTagSplit[0]
		var imageRef string
		if len(nameWithTagSplit) == 2 {
			name := strings.Split(nameWithTag, ":")[0]
			digest := strings.Split(image, "@")[1]
			imageRef = fmt.Sprintf("%s@%s", name, digest)
		} else {
			imageRef = nameWithTag
		}

		t.Run(imageRef, func(t *testing.T) {
			t.Parallel()

			ref, err := docker.ParseReference(fmt.Sprintf("//%s", imageRef))
			require.NoError(t, err)

			ctx := context.Background()
			img, err := ref.NewImage(ctx, nil)
			require.NoError(t, err)
			defer img.Close()

			_, _, err = img.Manifest(ctx)
			require.NoError(t, err)
		})
	}
}
