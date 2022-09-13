package openstack_helm

type Monitoring struct {
	Prometheus `yaml:"prometheus,omitempty"`
}

type Prometheus struct {
	Enabled bool `yaml:"enabled,omitempty"`
}

var MemcachedMonitoring Monitoring = Monitoring{
	Prometheus: Prometheus{
		Enabled: true,
	},
}
