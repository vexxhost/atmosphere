package steps

import (
	"context"
	"reflect"
	"time"

	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	log "github.com/sirupsen/logrus"
	"k8s.io/apimachinery/pkg/api/errors"
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

func (s *HelmReleaseStep) Execute(ctx context.Context) error {
	log := log.WithField("release", s.ReleaseName)

	release := &helmv2.HelmRelease{
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
	deployedRelease := &helmv2.HelmRelease{
		ObjectMeta: release.ObjectMeta,
	}

	err := s.Client.Get(ctx, client.ObjectKey{Name: s.ReleaseName, Namespace: s.Namespace}, deployedRelease)
	if client.IgnoreNotFound(err) != nil {
		return err
	}

	if errors.IsNotFound(err) {
		if err := s.Client.Create(ctx, release); err != nil {
			return err
		}

		log.Info("🚀 Helm release created")
	} else {
		if reflect.DeepEqual(deployedRelease.Spec, release.Spec) {
			log.Info("🚀 Helm release already up to date")
			return nil
		}

		deployedRelease.Spec = release.Spec
		if err := s.Client.Update(ctx, deployedRelease); err != nil {
			return err
		}

		log.Info("🚀 Helm release updated")
	}

	return nil
}

func (s *HelmReleaseStep) Validate(ctx context.Context) error {
	panic("TODO")
}
