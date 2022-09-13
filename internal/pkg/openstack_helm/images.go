package openstack_helm

import (
	"github.com/vexxhost/atmosphere/internal/pkg/images"
)

type Images struct {
	Tags ImageTags `yaml:"tags,omitempty"`
}

type ImageTags map[string]string

var MemcachedImages Images = Images{
	Tags: ImageTags{
		"memcached":                     images.GetReference("memcached", "docker.io/library/memcached", "1.6.17"),
		"prometheus_memcached_exporter": images.GetReference("memcached-exporter", "quay.io/prometheus/memcached-exporter", "v0.10.0"),
	},
}
