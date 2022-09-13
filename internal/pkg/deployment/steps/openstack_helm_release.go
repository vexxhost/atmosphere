package steps

import (
	"context"
	"fmt"
	"sync"

	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	log "github.com/sirupsen/logrus"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type OpenStackHelmReleaseStep struct {
	Client      client.Client
	Namespace   string
	ReleaseName string
	ChartSpec   helmv2.HelmChartTemplateSpec
}

func (s *OpenStackHelmReleaseStep) GetHelmReleaseStep() *HelmReleaseStep {
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

func (s *OpenStackHelmReleaseStep) Logger() *log.Entry {
	return s.GetHelmReleaseStep().Logger()
}

func (s *OpenStackHelmReleaseStep) Execute(ctx context.Context, wg *sync.WaitGroup) error {
	return s.GetHelmReleaseStep().Execute(ctx, wg)
}

func (s *OpenStackHelmReleaseStep) Validate(ctx context.Context) (*ValidationResult, error) {
	return s.GetHelmReleaseStep().Validate(ctx)
}
