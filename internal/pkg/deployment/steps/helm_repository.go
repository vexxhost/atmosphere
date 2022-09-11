package steps

import (
	"context"
	"reflect"
	"time"

	sourcev1 "github.com/fluxcd/source-controller/api/v1beta1"
	log "github.com/sirupsen/logrus"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type HelmRepositoryStep struct {
	Client    client.Client
	Namespace string
	Name      string
	URL       string
}

func (s *HelmRepositoryStep) Execute(ctx context.Context) error {
	log := log.WithField("repository", s.Name)

	repo := &sourcev1.HelmRepository{
		ObjectMeta: metav1.ObjectMeta{
			Name:      s.Name,
			Namespace: s.Namespace,
		},
		Spec: sourcev1.HelmRepositorySpec{
			URL: s.URL,
			Interval: metav1.Duration{
				Duration: time.Minute,
			},
			Timeout: &metav1.Duration{
				Duration: time.Minute,
			},
		},
	}
	deployedRepo := &sourcev1.HelmRepository{
		ObjectMeta: repo.ObjectMeta,
	}

	err := s.Client.Get(ctx, client.ObjectKey{Name: s.Name, Namespace: s.Namespace}, deployedRepo)
	if client.IgnoreNotFound(err) != nil {
		return err
	}

	if errors.IsNotFound(err) {
		if err := s.Client.Create(ctx, repo); err != nil {
			return err
		}

		log.Info("🚀 Helm repository created")
	} else {
		if reflect.DeepEqual(deployedRepo.Spec, repo.Spec) {
			log.Info("🚀 Helm repository already up to date")
			return nil
		}

		deployedRepo.Spec = repo.Spec
		if err := s.Client.Update(ctx, deployedRepo); err != nil {
			return err
		}

		log.Info("🚀 Helm repository updated")
	}

	return nil
}

func (s *HelmRepositoryStep) Validate(ctx context.Context) error {
	panic("TODO")
}
