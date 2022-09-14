package phases

import (
	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// NewHelmReleasesWithCrdPhase returns a list of steps that install Helm
// releases with CRDs.  We make sure to install those before any other Helm
// releases to make sure that we don't get any "missing API" errors.
func NewCrdHelmReleasePhase(kubeClient client.Client) Phase {
	return Phase{
		Steps: []steps.Step{
			&steps.CrdHelmReleaseStep{
				Client:      kubeClient,
				Namespace:   "openstack",
				ReleaseName: "pxc-operator",
				ApiGroup:    "pxc.percona.com",
				ChartSpec: helmv2.HelmChartTemplateSpec{
					Chart:     "pxc-operator",
					Version:   "1.10.0",
					SourceRef: PerconaSourceRef,
				},
				Values: map[string]interface{}{
					"nodeSelector": ControlPlaneNodeSelector,
				},
			},
			&steps.CrdHelmReleaseStep{
				Client:      kubeClient,
				Namespace:   "openstack",
				ReleaseName: "rabbitmq-cluster-operator",
				ApiGroup:    "rabbitmq.com",
				ChartSpec: helmv2.HelmChartTemplateSpec{
					Chart:     "rabbitmq-cluster-operator",
					Version:   "2.5.2",
					SourceRef: BitnamiSourceRef,
				},
				Values: map[string]interface{}{
					"rabbitmqImage": map[string]string{
						"repository": "library/rabbitmq",
						"tag":        "3.10.2-management",
					},
					"credentialUpdaterImage": map[string]string{
						"repository": "rabbitmqoperator/default-user-credential-updater",
						"tag":        "1.0.2",
					},
					"clusterOperator": map[string]interface{}{
						"image": map[string]string{
							"repository": "rabbitmqoperator/cluster-operator",
							"tag":        "1.13.1",
						},
						"fullnameOverride": "rabbitmq-cluster-operator",
						"nodeSelector":     ControlPlaneNodeSelector,
					},
					"msgTopologyOperator": map[string]interface{}{
						"image": map[string]string{
							"repository": "rabbitmqoperator/messaging-topology-operator",
							"tag":        "1.6.0",
						},
						"fullnameOverride": "rabbitmq-messaging-topology-operator",
						"nodeSelector":     ControlPlaneNodeSelector,
					},
					"useCertManager": true,
				},
			},
		},
	}
}
