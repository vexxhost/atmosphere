package openstack_helm

import (
	"fmt"

	"github.com/spf13/viper"
)

type Images struct {
	Tags ImageTags `yaml:"tags,omitempty"`
}

type ImageTags map[string]string

var MemcachedImages Images = Images{
	Tags: ImageTags{
		"memcached":                     GetImageRepository("docker.io/library", "memcached", "1.6.17"),
		"prometheus_memcached_exporter": GetImageRepository("quay.io/prometheus", "memcached-exporter", "v0.10.0"),
	},
}

func GetImageRepository(repository string, image string, tag string) string {
	var imageKey string

	if viper.IsSet("images.global.repository") {
		imageKey = "images.global.repository"
	} else {
		imageKey = fmt.Sprintf("images.%s.repository", image)
	}

	if len(imageKey) > 0 && viper.IsSet(imageKey) {
		repository = viper.GetString(imageKey)
	}

	return fmt.Sprintf("%s/%s:%s", repository, image, tag)
}
