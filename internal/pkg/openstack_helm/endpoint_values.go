package openstack_helm

import (
	"github.com/vexxhost/atmosphere/internal/pkg/yaml"
)

type EndpointValues struct {
	*Endpoints `yaml:"endpoints,omitempty"`
}

func (v *EndpointValues) ToString() (string, error) {
	return yaml.MarshallToString(v)
}
