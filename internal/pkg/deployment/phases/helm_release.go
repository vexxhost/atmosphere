package phases

import (
	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	"github.com/vexxhost/atmosphere/internal/pkg/images"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func NewHelmReleasePhase(client client.Client) Phase {
	return Phase{
		Steps: []steps.Step{
			&steps.HelmReleaseStep{
				Client:      client,
				Namespace:   "monitoring",
				ReleaseName: "node-feature-discovery",
				ChartSpec: helmv2.HelmChartTemplateSpec{
					Chart:             "node-feature-discovery",
					Version:           "0.11.2",
					ReconcileStrategy: "ChartVersion",
					SourceRef:         NodeFeatureDiscoverySourceRef,
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
			&steps.OpenStackHelmRelease{
				Client:      client,
				Namespace:   "openstack",
				ReleaseName: "memcached",
				ChartSpec: helmv2.HelmChartTemplateSpec{
					Chart:             "memcached",
					Version:           "0.1.6",
					ReconcileStrategy: "ChartVersion",
					SourceRef:         OpenstackHelmInfraSourceRef,
				},
			},
		},
	}
}
