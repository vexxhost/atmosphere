package deployment

import (
	"github.com/vexxhost/atmosphere/internal/pkg/openstack_helm"
	"github.com/vexxhost/atmosphere/internal/pkg/yaml"
)

type Config map[string]interface{}

var OpenstackHelmConfig Config = Config{
	"endpoints.yml":           &openstack_helm.EndpointsValues,
	"memcached.yml":           &openstack_helm.MemcachedValues,
	"memcached-overrides.yml": &openstack_helm.MemcachedValuesOverrides,
}

func (c Config) ToByteMap() map[string][]byte {
	var byteMap map[string][]byte = make(map[string][]byte)
	var err error

	for key, config := range c {
		byteMap[key], err = yaml.Marshall(config)
		if err != nil {
			panic(err)
		}
	}

	return byteMap
}
