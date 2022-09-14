package phases

import (
	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	"github.com/vexxhost/atmosphere/internal/pkg/images"
	v1 "k8s.io/api/core/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func NewOpenstackPhase(kubeClient client.Client) Phase {
	return Phase{
		Steps: []steps.Step{
			&steps.HelmReleaseStep{
				Client:      kubeClient,
				Namespace:   "monitoring",
				ReleaseName: "node-feature-discovery",
				ChartSpec: helmv2.HelmChartTemplateSpec{
					Chart:     "node-feature-discovery",
					Version:   "0.11.2",
					SourceRef: NodeFeatureDiscoverySourceRef,
				},
				Values: map[string]interface{}{
					"image": map[string]string{
						"repository": images.GetRepository("node-feature-discovery", "k8s.gcr.io/nfd/node-feature-discovery"),
					},
					"master": map[string]interface{}{
						"nodeSelector": ControlPlaneNodeSelector,
					},
				},
			},

			&steps.HelmReleaseStep{
				Client:      kubeClient,
				Namespace:   "openstack",
				ReleaseName: "ingress-nginx",
				ChartSpec: helmv2.HelmChartTemplateSpec{
					Chart:     "ingress-nginx",
					Version:   "4.0.17",
					SourceRef: IngressNginxSourceRef,
				},
				Values: map[string]interface{}{
					"controller": map[string]interface{}{
						"admissionWebhooks": map[string]int{
							"port": 7443,
						},
						"config": map[string]string{
							"proxy-buffer-size": "16k",
						},
						"dnsPolicy": v1.DNSClusterFirstWithHostNet,
						"extraArgs": map[string]string{
							"default-ssl-certificate": "ingress-nginx/wildcard",
						},
						"hostNetwork":  true,
						"ingressClass": "openstack",
						"ingressClassResource": map[string]string{
							"name": "openstack",
						},
						"kind":         "DaemonSet",
						"nodeSelector": ControlPlaneNodeSelector,
						"service": map[string]string{
							"type": "ClusterIP",
						},
					},
					"defaultBackend": map[string]bool{
						"enabled": true,
					},
				},
			},

			&steps.OpenStackHelmReleaseStep{
				Client:      kubeClient,
				Namespace:   "openstack",
				ReleaseName: "memcached",
				ChartSpec: helmv2.HelmChartTemplateSpec{
					Chart:     "memcached",
					Version:   "0.1.6",
					SourceRef: OpenstackHelmInfraSourceRef,
				},
			},

			&steps.OpenstackRabbitmqStep{
				Client: kubeClient,
				Name:   "keystone",
			},

			&steps.OpenstackRabbitmqStep{
				Client: kubeClient,
				Name:   "barbican",
			},

			&steps.OpenstackRabbitmqStep{
				Client: kubeClient,
				Name:   "glance",
			},

			&steps.OpenstackRabbitmqStep{
				Client: kubeClient,
				Name:   "cinder",
			},

			&steps.OpenstackRabbitmqStep{
				Client: kubeClient,
				Name:   "neutron",
			},

			&steps.OpenstackRabbitmqStep{
				Client: kubeClient,
				Name:   "nova",
			},

			&steps.OpenstackRabbitmqStep{
				Client: kubeClient,
				Name:   "senlin",
			},

			&steps.OpenstackRabbitmqStep{
				Client: kubeClient,
				Name:   "heat",
			},
		},
	}
}
