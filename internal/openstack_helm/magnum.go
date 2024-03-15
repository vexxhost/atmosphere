package openstack_helm

type MagnumConf struct {
	Database *DatabaseConf `yaml:"database,omitempty"`
}
