package openstack_helm

type HeatConf struct {
	Database *DatabaseConf `yaml:"database,omitempty"`
}
