package phases

import (
	"sigs.k8s.io/controller-runtime/pkg/client"

	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
)

func NewNamespacePhase(client client.Client) Phase {
	return Phase{
		Steps: []steps.Step{
			&steps.NamespaceStep{
				Client:    client,
				Namespace: "cert-manager",
			},
			&steps.NamespaceStep{
				Client:    client,
				Namespace: "monitoring",
			},
			&steps.NamespaceStep{
				Client:    client,
				Namespace: "openstack",
			},
		},
	}
}
