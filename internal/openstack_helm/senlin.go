package openstack_helm

type SenlinConf struct {
	API      SenlinAPIConf `yaml:"senlin_api"`
	Database *DatabaseConf `yaml:"database,omitempty"`
}

type SenlinAPIConf struct {
	Workers int32 `yaml:"workers"`
}
