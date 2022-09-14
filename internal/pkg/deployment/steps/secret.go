package steps

import (
	"context"
	"reflect"
	"sync"

	log "github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type SecretStep struct {
	Client    client.Client
	Namespace string
	Name      string
	Data      map[string][]byte
}

func (s *SecretStep) Logger() *log.Entry {
	return log.WithField("secret", s.Name)
}

func (s *SecretStep) Generate() *corev1.Secret {
	return &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      s.Name,
			Namespace: s.Namespace,
		},
		Data: s.Data,
	}
}

func (s *SecretStep) Get(ctx context.Context) (*corev1.Secret, error) {
	release := s.Generate()
	deployedSecret := &corev1.Secret{
		ObjectMeta: release.ObjectMeta,
	}

	err := s.Client.Get(ctx, client.ObjectKey{Name: s.Name, Namespace: s.Namespace}, deployedSecret)
	return deployedSecret, err
}

func (s *SecretStep) Execute(ctx context.Context, wg *sync.WaitGroup) error {
	defer wg.Done()

	validation, err := s.Validate(ctx)
	if err != nil {
		return err
	}

	secret := s.Generate()

	if !validation.Installed {
		if err := s.Client.Create(ctx, secret); err != nil {
			return err
		}

		s.Logger().Info("🚀 Secret created")
	} else if !validation.Updated {
		deployedSecret, err := s.Get(ctx)
		if err != nil {
			return err
		}

		deployedSecret.Data = secret.Data
		if err := s.Client.Update(ctx, deployedSecret); err != nil {
			return err
		}
		s.Logger().Info("🚀 Secret updated")
	}

	return nil
}

func (s *SecretStep) Validate(ctx context.Context) (*ValidationResult, error) {
	deployedSecret, err := s.Get(ctx)
	if client.IgnoreNotFound(err) != nil {
		return nil, err
	}

	if errors.IsNotFound(err) {
		s.Logger().Info("⏳ Secret missing from Kubernetes")
		return &ValidationResult{
			Installed: false,
			Updated:   false,
			Tested:    false,
		}, nil
	}

	secret := s.Generate()
	if !reflect.DeepEqual(deployedSecret.Data, secret.Data) {
		s.Logger().Info("⏳ Secret configuration needs to be updated")
		return &ValidationResult{
			Installed: true,
			Updated:   false,
			Tested:    false,
		}, nil
	}

	s.Logger().Info("🚀 Secret is up to date")
	return &ValidationResult{
		Installed: true,
		Updated:   true,
		Tested:    true,
	}, nil
}
