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

func (s *HelmRepositoryStep) Logger() *log.Entry {
	return log.WithField("repository", s.Name)
}

func (s *HelmRepositoryStep) GenerateHelmRepository() *sourcev1.HelmRepository {
	return &sourcev1.HelmRepository{
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
}

func (s *HelmRepositoryStep) GetHelmRepository(ctx context.Context) (*sourcev1.HelmRepository, error) {
	repo := s.GenerateHelmRepository()
	deployedRepo := &sourcev1.HelmRepository{
		ObjectMeta: repo.ObjectMeta,
	}

	err := s.Client.Get(ctx, client.ObjectKey{Name: s.Name, Namespace: s.Namespace}, deployedRepo)
	return deployedRepo, err
}

func (s *HelmRepositoryStep) Execute(ctx context.Context) error {
	validation, err := s.Validate(ctx)
	if err != nil {
		return err
	}

	repo := s.GenerateHelmRepository()

	if !validation.Installed {
		if err := s.Client.Create(ctx, repo); err != nil {
			return err
		}

		s.Logger().Info("🚀 Helm repository created")
	} else if !validation.Updated {
		deployedRepo, err := s.GetHelmRepository(ctx)
		if err != nil {
			return err
		}

		deployedRepo.Spec = repo.Spec
		if err := s.Client.Update(ctx, deployedRepo); err != nil {
			return err
		}
		s.Logger().Info("🚀 Helm repository updated")
	}

	return nil
}

func (s *HelmRepositoryStep) Validate(ctx context.Context) (*ValidationResult, error) {
	repo := s.GenerateHelmRepository()
	deployedRepo, err := s.GetHelmRepository(ctx)
	if client.IgnoreNotFound(err) != nil {
		return nil, err
	}

	if errors.IsNotFound(err) {
		s.Logger().Info("⏳ Helm repository missing from cluster")
		return &ValidationResult{
			Installed: false,
			Updated:   false,
			Tested:    false,
		}, nil
	}

	if !reflect.DeepEqual(deployedRepo.Spec, repo.Spec) {
		s.Logger().Info("⏳ Helm repository configuration needs to be updated")
		return &ValidationResult{
			Installed: true,
			Updated:   false,
			Tested:    false,
		}, nil
	}

	s.Logger().Info("🚀 Helm repository is up to date")
	return &ValidationResult{
		Installed: true,
		Updated:   true,
		Tested:    true,
	}, nil
}
