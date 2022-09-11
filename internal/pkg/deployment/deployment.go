package deployment

import (
	"context"

	log "github.com/sirupsen/logrus"
	"sigs.k8s.io/controller-runtime/pkg/client"

	"github.com/vexxhost/atmosphere/internal/pkg/kubernetes"
)

type Deployment struct {
	client  client.Client
	context context.Context
}

func NewDeployment() (*Deployment, error) {
	client, err := kubernetes.GetClient()
	if err != nil {
		return nil, err
	}

	return &Deployment{
		client:  client,
		context: context.TODO(),
	}, nil
}

func (d *Deployment) Execute() error {
	if err := d.EnsureNamespace(); err != nil {
		log.WithError(err).Fatal("💥 Failed to create namespace")
	}

	if err := d.EnsureMemcached(); err != nil {
		log.WithError(err).Fatal("💥 Failed to deploy Memcached")
	}

	return nil
}
