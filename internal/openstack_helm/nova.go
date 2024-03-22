package openstack_helm

type NovaConf struct {
	Database *DatabaseConf `yaml:"database,omitempty"`
}
