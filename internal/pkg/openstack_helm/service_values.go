package openstack_helm

import (
	"github.com/vexxhost/atmosphere/internal/pkg/yaml"
)

type ServiceValues struct {
	*Images     `yaml:"images,omitempty"`
	*Monitoring `yaml:"monitoring,omitempty"`
}

func NewServiceValuesFromChart(chart string) *ServiceValues {
	return &ServiceValues{
		Images:     NewImagesFromChart(chart),
		Monitoring: NewMonitoringFromChart(chart),
	}
}

func (v *ServiceValues) ToString() (string, error) {
	return yaml.MarshallToString(v)
}
