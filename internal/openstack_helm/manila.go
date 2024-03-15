package openstack_helm

type ManilaConf struct {
	Database *DatabaseConf `yaml:"database,omitempty"`
}
