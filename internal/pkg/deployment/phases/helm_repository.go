package phases

import (
	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func NewHelmRepositoryPhase(kubeClient client.Client) Phase {
	return Phase{
		Steps: []steps.Step{
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: "kube-system",
				Name:      "ceph",
				URL:       "https://ceph.github.io/csi-charts",
			},
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: CertManagerSourceRef.Namespace,
				Name:      CertManagerSourceRef.Name,
				URL:       "https://charts.jetstack.io",
			},
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: "monitoring",
				Name:      "prometheus-community",
				URL:       "https://prometheus-community.github.io/helm-charts",
			},
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: NodeFeatureDiscoverySourceRef.Namespace,
				Name:      NodeFeatureDiscoverySourceRef.Name,
				URL:       "https://kubernetes-sigs.github.io/node-feature-discovery/charts",
			},
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: IngressNginxSourceRef.Namespace,
				Name:      IngressNginxSourceRef.Name,
				URL:       "https://kubernetes.github.io/ingress-nginx",
			},
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: "openstack",
				Name:      "percona",
				URL:       "https://percona.github.io/percona-helm-charts/",
			},
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: "openstack",
				Name:      "bitnami",
				URL:       "https://charts.bitnami.com/bitnami",
			},
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: "openstack",
				Name:      "coredns",
				URL:       "https://coredns.github.io/helm",
			},
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: OpenstackHelmInfraSourceRef.Namespace,
				Name:      OpenstackHelmInfraSourceRef.Name,
				URL:       "https://tarballs.opendev.org/openstack/openstack-helm-infra/",
			},
			&steps.HelmRepositoryStep{
				Client:    kubeClient,
				Namespace: "openstack",
				Name:      "openstack-helm",
				URL:       "https://tarballs.opendev.org/openstack/openstack-helm/",
			},
		},
	}
}
