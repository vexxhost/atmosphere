package phases

import (
	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func NewHelmRepositoryPhase(client client.Client) Phase {
	return Phase{
		Steps: []steps.Step{
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "kube-system",
				Name:      "ceph",
				URL:       "https://ceph.github.io/csi-charts",
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "cert-manager",
				Name:      "jetstack",
				URL:       "https://charts.jetstack.io",
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "monitoring",
				Name:      "prometheus-community",
				URL:       "https://prometheus-community.github.io/helm-charts",
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "monitoring",
				Name:      "node-feature-discovery",
				URL:       "https://kubernetes-sigs.github.io/node-feature-discovery/charts",
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "openstack",
				Name:      "ingress-nginx",
				URL:       "https://kubernetes.github.io/ingress-nginx",
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "openstack",
				Name:      "percona",
				URL:       "https://percona.github.io/percona-helm-charts/",
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "openstack",
				Name:      "bitnami",
				URL:       "https://charts.bitnami.com/bitnami",
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "openstack",
				Name:      "openstack-helm-infra",
				URL:       "https://tarballs.opendev.org/openstack/openstack-helm-infra/",
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "openstack",
				Name:      "coredns",
				URL:       "https://coredns.github.io/helm",
			},
			&steps.HelmRepositoryStep{
				Client:    client,
				Namespace: "openstack",
				Name:      "openstack-helm",
				URL:       "https://tarballs.opendev.org/openstack/openstack-helm/",
			},
		},
	}
}
