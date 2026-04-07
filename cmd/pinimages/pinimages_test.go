package main

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGetImageNameToPull(t *testing.T) {
	tests := []struct {
		image   string
		release string
		want    string
	}{
		{
			image:   "{{ atmosphere_image_prefix }}quay.io/ceph/ceph:v18.2.2",
			release: "2024.1",
			want:    "quay.io/ceph/ceph:v18.2.2",
		},
		{
			image:   "{{ atmosphere_image_prefix }}registry.atmosphere.dev/library/glance:{{ atmosphere_release }}",
			release: "2024.1",
			want:    "registry.atmosphere.dev/library/glance:2024.1",
		},
	}

	for _, tt := range tests {
		t.Run(tt.image, func(t *testing.T) {
			got := GetImageNameToPull(tt.image, tt.release)

			assert.Equal(t, tt.want, got)
		})
	}
}
