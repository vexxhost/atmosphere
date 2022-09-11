package openstack_helm

type Images struct {
	Tags ImageTags `yaml:"tags,omitempty"`
}

type ImageTags map[string]string

func NewImagesFromChart(chart string) *Images {
	return &Images{
		Tags: ImageTags{
			"memcached":                     "quay.io/vexxhost/memcached:1.6.9",
			"prometheus_memcached_exporter": "quay.io/vexxhost/memcached-exporter:v0.9.0-1",
		},
	}
}
