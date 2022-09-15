package deployment

import (
	"context"

	"sigs.k8s.io/controller-runtime/pkg/client"

	"github.com/vexxhost/atmosphere/internal/pkg/deployment/phases"
	"github.com/vexxhost/atmosphere/internal/pkg/kubernetes"
)

type Deployment struct {
	Namespace string
	Phases    []phases.Phase

	client  client.Client
	context context.Context
}

func NewDeployment() (*Deployment, error) {
	client, err := kubernetes.GetClient()
	if err != nil {
		return nil, err
	}

	return &Deployment{
		Namespace: "openstack",

		Phases: []phases.Phase{
			phases.NewNamespacePhase(client),
			phases.NewConfigPhase(client),
			phases.NewHelmRepositoryPhase(client),
			phases.NewCertManagerPhase(client),
			phases.NewCrdHelmReleasePhase(client),
			phases.NewOpenstackPhase(client),
		},

		client:  client,
		context: context.TODO(),
	}, nil
}

func (d *Deployment) Execute(diff bool) error {
	for _, phase := range d.Phases {
		if err := phase.Execute(d.context, diff); err != nil {
			return err
		}
	}

	return nil
}

func (d *Deployment) Validate(diff bool) error {
	for _, phase := range d.Phases {
		if err := phase.Validate(d.context, diff); err != nil {
			return err
		}
	}

	return nil
}
