package defaults

import (
	"regexp"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

var (
	r *regexp.Regexp
)

func init() {
	r, _ = regexp.Compile(`{{ atmosphere_proxy_cache_prefix }}{{ atmosphere_images\['(?P<ImageName>\w+)'] \| vexxhost.kubernetes.docker_image\('ref'\) }}`)
}

func AssertAtmosphereImage(t *testing.T, expected string, value string) {
	matches := r.FindStringSubmatch(value)
	require.Len(t, matches, 2)
	imageName := matches[1]

	image, err := GetImageByKey(imageName)
	require.NoError(t, err)

	assert.Equal(t, expected, image)
}
