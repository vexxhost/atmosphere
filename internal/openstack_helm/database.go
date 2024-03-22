package openstack_helm

type DatabaseConf struct {
	ConnectionRecycleTime int `yaml:"connection_recycle_time,omitempty"`
	MaxPoolSize           int `yaml:"max_pool_size,omitempty"`
	MaxRetries            int `yaml:"max_retries,omitempty"`
}
