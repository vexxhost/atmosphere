package openstack_helm

type MemcachedConf struct {
	Database *DatabaseConf `yaml:"database,omitempty"`
}
