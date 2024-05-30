package openstack_helm

import (
	"gopkg.in/yaml.v2"
	"helm.sh/helm/v3/pkg/chart/loader"
	"helm.sh/helm/v3/pkg/chartutil"
)

type HelmValues struct {
	Conf `yaml:"conf"`
}

type Conf struct {
	Barbican  *BarbicanConf  `yaml:"barbican,omitempty"`
	Cinder    *CinderConf    `yaml:"cinder,omitempty"`
	Designate *DesignateConf `yaml:"designate,omitempty"`
	Glance    *GlanceConf    `yaml:"glance,omitempty"`
	Heat      *HeatConf      `yaml:"heat,omitempty"`
	Keystone  *KeystoneConf  `yaml:"keystone,omitempty"`
	Magnum    *MagnumConf    `yaml:"magnum,omitempty"`
	Manila    *ManilaConf    `yaml:"manila,omitempty"`
	Neutron   *NeutronConf   `yaml:"neutron,omitempty"`
	Nova      *NovaConf      `yaml:"nova,omitempty"`
	Octavia   *OctaviaConf   `yaml:"octavia,omitempty"`
	Placement *PlacementConf `yaml:"placement,omitempty"`
	Staffeln  *StaffelnConf  `yaml:"staffeln,omitempty"`
}

func (h *HelmValues) YAML() ([]byte, error) {
	return yaml.Marshal(h)
}

func (h *HelmValues) NativeHelmValues() (chartutil.Values, error) {
	yamlData, err := h.YAML()
	if err != nil {
		return nil, err
	}

	return chartutil.ReadValues(yamlData)
}

func FromYAML(yamlData []byte) (*HelmValues, error) {
	var helmValues HelmValues
	err := yaml.Unmarshal(yamlData, &helmValues)
	if err != nil {
		return nil, err
	}

	return &helmValues, nil
}

func FromYAMLString(yamlString string) (*HelmValues, error) {
	return FromYAML([]byte(yamlString))
}

func CoalescedHelmValues(name string, values *HelmValues) (*HelmValues, error) {
	chart, err := loader.Load(name)
	if err != nil {
		return nil, err
	}

	releaseValues, err := values.NativeHelmValues()
	if err != nil {
		return nil, err
	}

	mergedValues, err := chartutil.CoalesceValues(chart, releaseValues)
	if err != nil {
		return nil, err
	}

	yamlData, err := mergedValues.YAML()
	if err != nil {
		return nil, err
	}

	return FromYAMLString(yamlData)
}
