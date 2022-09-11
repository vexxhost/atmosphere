package openstack_helm

import (
	"fmt"

	"github.com/spf13/viper"
	"github.com/vexxhost/atmosphere/internal/pkg/yaml"
	corev1 "k8s.io/client-go/applyconfigurations/core/v1"
	metav1 "k8s.io/client-go/applyconfigurations/meta/v1"
	"k8s.io/utils/pointer"
)

func GetConfigSecret() (*corev1.SecretApplyConfiguration, error) {
	secret := &corev1.SecretApplyConfiguration{
		TypeMetaApplyConfiguration: metav1.TypeMetaApplyConfiguration{
			APIVersion: pointer.StringPtr("v1"),
			Kind:       pointer.StringPtr("Secret"),
		},
		ObjectMetaApplyConfiguration: &metav1.ObjectMetaApplyConfiguration{
			Name:      pointer.StringPtr("openstack-helm-config"),
			Namespace: pointer.StringPtr("openstack"),
		},
		StringData: map[string]string{},
	}

	// Endpoints
	endpoints, err := NewEndpointValues().ToString()
	if err != nil {
		return nil, err
	}
	secret.StringData["endpoints.yml"] = endpoints

	// Overrides
	for _, svc := range SERVICES {
		err := AddServiceConfigForService(svc, secret)
		if err != nil {
			return nil, err
		}
	}

	return secret, nil
}

func AddServiceConfigForService(service string, secret *corev1.SecretApplyConfiguration) error {
	enabledKey := fmt.Sprintf("%s.enabled", service)
	viper.SetDefault(enabledKey, true)

	if !viper.GetBool(enabledKey) {
		return nil
	}

	serviceValues, err := NewServiceValuesFromChart(service).ToString()
	if err != nil {
		return err
	}
	valuesFileName := fmt.Sprintf("%s.yml", service)
	secret.StringData[valuesFileName] = serviceValues

	overrides, err := GetOverridesForServiceInYAML(service)
	if err != nil {
		return err
	}
	overridesFileName := fmt.Sprintf("%s-overrides.yml", service)
	secret.StringData[overridesFileName] = overrides

	return nil
}

func GetOverridesForService(service string) map[string]interface{} {
	overridesKey := fmt.Sprintf("%s.overrides", service)
	return viper.GetStringMap(overridesKey)
}

func GetOverridesForServiceInYAML(service string) (string, error) {
	overrides := GetOverridesForService(service)

	return yaml.MarshallToString(overrides)
}
