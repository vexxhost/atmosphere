package steps

import (
	"context"
	"sync"

	log "github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
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

func (s *NamespaceStep) Generate() *corev1.Namespace {
	return &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: s.Namespace,
		},
	}
}

func (s *NamespaceStep) Get(ctx context.Context) (*corev1.Namespace, error) {
	namespace := s.Generate()
	deployedNamespace := &corev1.Namespace{
		ObjectMeta: namespace.ObjectMeta,
	}

	err := s.Client.Get(ctx, client.ObjectKey{Name: s.Namespace}, deployedNamespace)
	return deployedNamespace, err
}

func (s *NamespaceStep) Execute(ctx context.Context, wg *sync.WaitGroup) error {
	defer wg.Done()

	validation, err := s.Validate(ctx)
	if err != nil {
		return err
	}

	namespace := s.Generate()

	if !validation.Installed {
		if err := s.Client.Create(ctx, namespace); err != nil {
			return err
		}

		s.Logger().Info("🚀 Namespace created")
	}

	return nil
}

func (s *NamespaceStep) Validate(ctx context.Context) (*ValidationResult, error) {
	_, err := s.Get(ctx)
	if client.IgnoreNotFound(err) != nil {
		return nil, err
	}

	if errors.IsNotFound(err) {
		s.Logger().Info("⏳ Namespace missing from cluster")
		return &ValidationResult{
			Installed: false,
			Updated:   false,
			Tested:    false,
		}, nil
	}

	s.Logger().Info("🚀 Namespace is up to date")
	return &ValidationResult{
		Installed: true,
		Updated:   true,
		Tested:    true,
	}, nil
}
