package openstack_helm

type Monitoring struct {
	Prometheus `yaml:"prometheus,omitempty"`
}

type Prometheus struct {
	Enabled bool `yaml:"enabled,omitempty"`
}

func NewMonitoringFromChart(chart string) *Monitoring {
	return &Monitoring{
		Prometheus: Prometheus{
			Enabled: true,
		},
	}
}
