package openstack_helm

import (
	"fmt"

	"github.com/spf13/viper"
)

type Values struct {
	*Images     `yaml:"images,omitempty"`
	*Endpoints  `yaml:"endpoints,omitempty"`
	*Monitoring `yaml:"monitoring,omitempty"`
}

var EndpointsValues Values = Values{
	Endpoints: &OpenstackHelmEndpoints,
}

var MemcachedValues Values = Values{
	Images:     &MemcachedImages,
	Monitoring: &MemcachedMonitoring,
}
var MemcachedValuesOverrides = GetOverridesForService("memcached")

func GetOverridesForService(service string) map[string]interface{} {
	overridesKey := fmt.Sprintf("%s.overrides", service)
	return viper.GetStringMap(overridesKey)
}
