package openstack_helm

type IronicConf struct {
	Database *DatabaseConf `yaml:"database,omitempty"`
}
