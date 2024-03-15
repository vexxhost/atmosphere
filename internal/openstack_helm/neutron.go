package openstack_helm

type NeutronConf struct {
	Database *DatabaseConf `yaml:"database,omitempty"`
}
