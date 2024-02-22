package defaults

import (
	"context"
	"fmt"
	"slices"
	"strings"
	"testing"

	"github.com/containers/image/v5/docker"
	"github.com/stretchr/testify/require"
)

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
		nameWithTag := strings.Split(image, "@")[0]
		name := strings.Split(nameWithTag, ":")[0]
		digest := strings.Split(image, "@")[1]
		image := fmt.Sprintf("%s@%s", name, digest)

		t.Run(image, func(t *testing.T) {
			t.Parallel()

			ref, err := docker.ParseReference(fmt.Sprintf("//%s", image))
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
