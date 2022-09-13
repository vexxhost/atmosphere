package steps

import (
	"context"
	"sync"
	"time"

	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	log "github.com/sirupsen/logrus"
	"github.com/vexxhost/atmosphere/internal/pkg/kubernetes"
	"k8s.io/apimachinery/pkg/util/wait"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type CrdHelmReleaseStep struct {
	Client      client.Client
	Namespace   string
	ReleaseName string
	ApiGroup    string
	ChartSpec   helmv2.HelmChartTemplateSpec
	Values      map[string]interface{}
}

func (s *CrdHelmReleaseStep) GetHelmReleaseStep() *HelmReleaseStep {
	return &HelmReleaseStep{
		Client:      s.Client,
		Namespace:   s.Namespace,
		ReleaseName: s.ReleaseName,
		ChartSpec:   s.ChartSpec,
		Values:      s.Values,
	}
}

func (s *CrdHelmReleaseStep) Logger() *log.Entry {
	return s.GetHelmReleaseStep().Logger()
}

func (s *CrdHelmReleaseStep) Execute(ctx context.Context, wg *sync.WaitGroup) error {
	defer wg.Done()

	wg.Add(1)
	err := s.GetHelmReleaseStep().Execute(ctx, wg)
	if err != nil {
		return err
	}

	discoveryClient, err := kubernetes.GetDiscoveryClient()
	if err != nil {
		log.WithError(err).Fatal("Failed to get discovery client")
		return err
	}

	err = wait.PollImmediate(5*time.Second, 10*time.Minute, func() (bool, error) {
		apiGroup, _, err := discoveryClient.ServerGroupsAndResources()
		if err != nil {
			log.WithError(err).Fatal("Failed to list groups and resources")
		}

		for _, group := range apiGroup {
			if group.Name == s.ApiGroup {
				return true, nil
			}
		}

		return false, nil
	})

	if err != nil {
		log.WithError(err).Fatal("Failed to wait for CRD to be available")
	}

	return nil
}

func (s *CrdHelmReleaseStep) Validate(ctx context.Context) (*ValidationResult, error) {
	return s.GetHelmReleaseStep().Validate(ctx)
}
