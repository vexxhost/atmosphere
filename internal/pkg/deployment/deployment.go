package deployment

import (
	"context"
	"sync"

	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	"sigs.k8s.io/controller-runtime/pkg/client"

	"github.com/vexxhost/atmosphere/internal/pkg/deployment/phases"
	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	"github.com/vexxhost/atmosphere/internal/pkg/kubernetes"
)

type Deployment struct {
	Namespace string
	Phases    []phases.Phase
	Steps     []steps.Step

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
		},

		Steps: []steps.Step{
			&steps.OpenStackHelmRelease{
				Client:      client,
				Namespace:   "openstack",
				ReleaseName: "memcached",
				ChartSpec: helmv2.HelmChartTemplateSpec{
					Chart:             "memcached",
					Version:           "0.1.6",
					ReconcileStrategy: "ChartVersion",
					SourceRef: helmv2.CrossNamespaceObjectReference{
						Kind: "HelmRepository",
						Name: "openstack-helm-infra",
					},
				},
			},
		},

		client:  client,
		context: context.TODO(),
	}, nil
}

func (d *Deployment) Execute() error {
	for _, phase := range d.Phases {
		if err := phase.Execute(d.context); err != nil {
			return err
		}
	}

	var wg sync.WaitGroup
	for _, step := range d.Steps {
		wg.Add(1)
		go step.Execute(d.context, &wg)
	}

	return nil
}

func (d *Deployment) Validate() error {
	for _, phase := range d.Phases {
		if err := phase.Validate(d.context); err != nil {
			return err
		}
	}

	for _, step := range d.Steps {
		if _, err := step.Validate(d.context); err != nil {
			return err
		}
	}

	return nil
}
