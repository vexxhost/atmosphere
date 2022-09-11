package steps

import (
	"context"
	"fmt"

	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type OpenStackHelmRelease struct {
	Client      client.Client
	Namespace   string
	ReleaseName string
	ChartSpec   helmv2.HelmChartTemplateSpec
}

func (s *OpenStackHelmRelease) GetHelmReleaseStep() *HelmReleaseStep {
	return &HelmReleaseStep{
		Client:      s.Client,
		Namespace:   s.Namespace,
		ReleaseName: s.ReleaseName,
		ChartSpec:   s.ChartSpec,
		ValuesFrom: []helmv2.ValuesReference{
			{
				Kind:      "Secret",
				Name:      "openstack-helm-config",
				ValuesKey: "endpoints.yml",
			},
			{
				Kind:      "Secret",
				Name:      "openstack-helm-config",
				ValuesKey: fmt.Sprintf("%s.yml", s.ReleaseName),
			},
			{
				Kind:      "Secret",
				Name:      "openstack-helm-config",
				ValuesKey: fmt.Sprintf("%s-overrides.yml", s.ReleaseName),
			},
		},
	}
}

func (s *OpenStackHelmRelease) Execute(ctx context.Context) error {
	return s.GetHelmReleaseStep().Execute(ctx)
}

func (s *OpenStackHelmRelease) Validate(ctx context.Context) error {
	return s.GetHelmReleaseStep().Validate(ctx)
}
