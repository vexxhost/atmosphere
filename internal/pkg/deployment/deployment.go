package deployment

import (
	"context"

	log "github.com/sirupsen/logrus"
)

type Deployment struct {
	context context.Context
}

func NewDeployment() *Deployment {
	return &Deployment{
		context: context.TODO(),
	}
}

func (d *Deployment) Execute() error {
	if err := d.CreateNamespace(); err != nil {
		log.WithError(err).Fatal("💥 Failed to create namespace")
	}
	log.Info("🚀 Created namespace")

	return nil
}
