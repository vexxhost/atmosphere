package openstack_helm

type KeystoneConf struct {
	Database *DatabaseConf `yaml:"database,omitempty"`
}
