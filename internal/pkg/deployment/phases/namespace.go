package phases

import (
	"sigs.k8s.io/controller-runtime/pkg/client"

	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
)

func NewNamespacePhase(kubeClient client.Client) Phase {
	return Phase{
		Steps: []steps.Step{
			&steps.NamespaceStep{
				Client:    kubeClient,
				Namespace: "cert-manager",
			},
			&steps.NamespaceStep{
				Client:    kubeClient,
				Namespace: "monitoring",
			},
			&steps.NamespaceStep{
				Client:    kubeClient,
				Namespace: "openstack",
			},
		},
	}
}
