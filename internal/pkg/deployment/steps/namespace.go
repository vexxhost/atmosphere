package steps

import (
	"context"

	log "github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

type NamespaceStep struct {
	Client    client.Client
	Namespace string
}

func (s *NamespaceStep) Logger() *log.Entry {
	return log.WithField("namespace", s.Namespace)
}

func (s *NamespaceStep) GenerateNamespace() *corev1.Namespace {
	return &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: s.Namespace,
		},
	}
}

func (s *NamespaceStep) Execute(ctx context.Context) error {
	validation, err := s.Validate(ctx)
	if err != nil {
		return err
	}

	namespace := s.GenerateNamespace()

	if !validation.Installed {
		if err := s.Client.Create(ctx, namespace); err != nil {
			return err
		}

		s.Logger().Info("🚀 Namespace created")
	}

	return nil
}

func (s *NamespaceStep) Validate(ctx context.Context) (*ValidationResult, error) {
	ns := &corev1.Namespace{}
	if err := s.Client.Get(ctx, client.ObjectKey{Name: s.Namespace}, ns); err != nil {
		return nil, err
	}

	s.Logger().Info("🚀 Namespace is up to date")
	return &ValidationResult{
		Installed: true,
		Updated:   true,
		Tested:    true,
	}, nil
}
