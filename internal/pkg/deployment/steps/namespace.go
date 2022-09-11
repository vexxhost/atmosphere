package steps

import (
	"context"

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

func (s *NamespaceStep) Execute(ctx context.Context) error {
	log := log.WithField("namespace", s.Namespace)
	namespace := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: s.Namespace,
		},
	}

	err := s.Client.Get(ctx, client.ObjectKey{Name: s.Namespace}, namespace)
	if client.IgnoreNotFound(err) != nil {
		return err
	}

	if errors.IsNotFound(err) {
		if err := s.Client.Create(ctx, namespace); err != nil {
			return err
		}
		log.Info("🚀 Namespace created")
	} else {
		log.Info("🚀 Namespace already exists")
	}

	return nil
}

func (s *NamespaceStep) Validate(ctx context.Context) error {
	ns := &corev1.Namespace{}
	if err := s.Client.Get(ctx, client.ObjectKey{Name: s.Namespace}, ns); err != nil {
		return err
	}

	log.Info("🚀 Namespace validated")
	return nil
}
