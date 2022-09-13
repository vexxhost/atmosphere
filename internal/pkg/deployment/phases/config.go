package phases

import (
	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	"github.com/vexxhost/atmosphere/internal/pkg/openstack_helm"
	"github.com/vexxhost/atmosphere/internal/pkg/yaml"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type Config map[string]interface{}

var OpenstackHelmConfig Config = Config{
	"endpoints.yml":           &openstack_helm.EndpointsValues,
	"memcached.yml":           &openstack_helm.MemcachedValues,
	"memcached-overrides.yml": &openstack_helm.MemcachedValuesOverrides,
}

func (c Config) ToByteMap() map[string][]byte {
	var byteMap map[string][]byte = make(map[string][]byte)
	var err error

	for key, config := range c {
		byteMap[key], err = yaml.Marshall(config)
		if err != nil {
			panic(err)
		}
	}

	return byteMap
}

func NewConfigPhase(kubeClient client.Client) Phase {
	return Phase{
		Steps: []steps.Step{
			&steps.SecretStep{
				Client:    kubeClient,
				Namespace: "openstack",
				Name:      "openstack-helm-config",
				Data:      OpenstackHelmConfig.ToByteMap(),
			},
		},
	}
}
