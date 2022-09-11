package steps

import (
	"context"
	"reflect"
	"time"

	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	fluxmeta "github.com/fluxcd/pkg/apis/meta"
	log "github.com/sirupsen/logrus"
	"k8s.io/apimachinery/pkg/api/errors"
	apimeta "k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type HelmReleaseStep struct {
	Client      client.Client
	Namespace   string
	ReleaseName string
	ChartSpec   helmv2.HelmChartTemplateSpec
	ValuesFrom  []helmv2.ValuesReference
}

func (s *HelmReleaseStep) Logger() *log.Entry {
	return log.WithField("release", s.ReleaseName)
}

func (s *HelmReleaseStep) Generate() *helmv2.HelmRelease {
	return &helmv2.HelmRelease{
		ObjectMeta: metav1.ObjectMeta{
			Name:      s.ReleaseName,
			Namespace: s.Namespace,
		},
		Spec: helmv2.HelmReleaseSpec{
			Chart: helmv2.HelmChartTemplate{
				Spec: s.ChartSpec,
			},
			Interval: metav1.Duration{
				Duration: time.Minute,
			},
			ValuesFrom: s.ValuesFrom,
		},
	}
}

func (s *HelmReleaseStep) Get(ctx context.Context) (*helmv2.HelmRelease, error) {
	release := s.Generate()
	deployedRelease := &helmv2.HelmRelease{
		ObjectMeta: release.ObjectMeta,
	}

	err := s.Client.Get(ctx, client.ObjectKey{Name: s.ReleaseName, Namespace: s.Namespace}, deployedRelease)
	return deployedRelease, err
}

func (s *HelmReleaseStep) Execute(ctx context.Context) error {
	validation, err := s.Validate(ctx)
	if err != nil {
		return err
	}

	release := s.Generate()

	if !validation.Installed {
		if err := s.Client.Create(ctx, release); err != nil {
			return err
		}

		s.Logger().Info("🚀 Helm release created")
	} else if !validation.Updated {
		deployedRelease, err := s.Get(ctx)
		if err != nil {
			return err
		}

		deployedRelease.Spec = release.Spec
		if err := s.Client.Update(ctx, deployedRelease); err != nil {
			return err
		}
		s.Logger().Info("🚀 Helm release updated")
	}

	return nil
}

func (s *HelmReleaseStep) Validate(ctx context.Context) (*ValidationResult, error) {
	deployedRelease, err := s.Get(ctx)
	if client.IgnoreNotFound(err) != nil {
		return nil, err
	}

	if errors.IsNotFound(err) {
		s.Logger().Info("⏳ Helm release missing from cluster")
		return &ValidationResult{
			Installed: false,
			Updated:   false,
			Tested:    false,
		}, nil
	}

	release := s.Generate()
	if !reflect.DeepEqual(deployedRelease.Spec, release.Spec) {
		s.Logger().Info("⏳ Helm release configuration needs to be updated")
		return &ValidationResult{
			Installed: true,
			Updated:   false,
			Tested:    false,
		}, nil
	}

	releaseReady := apimeta.IsStatusConditionTrue(deployedRelease.Status.Conditions, fluxmeta.ReadyCondition)
	releaseStatus := apimeta.IsStatusConditionTrue(deployedRelease.Status.Conditions, helmv2.ReleasedCondition)

	if !releaseStatus || !releaseReady {
		s.Logger().Info("⏳ Helm release is not ready")
		return &ValidationResult{
			Installed: true,
			Updated:   true,
			Tested:    false,
		}, nil
	}

	s.Logger().Info("🚀 Helm release is up to date")
	return &ValidationResult{
		Installed: true,
		Updated:   true,
		Tested:    true,
	}, nil
}
