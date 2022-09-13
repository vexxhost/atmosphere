package deployment

import (
	"context"

	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	"sigs.k8s.io/controller-runtime/pkg/client"

	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	"github.com/vexxhost/atmosphere/internal/pkg/kubernetes"
)

type Deployment struct {
	Namespace string
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

		Steps: []steps.Step{
			&steps.NamespaceStep{
				Client:    client,
				Namespace: "openstack",
			},
			&steps.SecretStep{
				Client:    client,
				Namespace: "openstack",
				Name:      "openstack-helm-config",
				Data:      OpenstackHelmConfig.ToByteMap(),
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "openstack",
				Name:      "openstack-helm-infra",
				URL:       "https://tarballs.opendev.org/openstack/openstack-helm-infra/",
			},
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
	for _, step := range d.Steps {
		if err := step.Execute(d.context); err != nil {
			return err
		}
	}

	return nil
}

func (d *Deployment) Validate() error {
	for _, step := range d.Steps {
		if _, err := step.Validate(d.context); err != nil {
			return err
		}
	}

	return nil
}
