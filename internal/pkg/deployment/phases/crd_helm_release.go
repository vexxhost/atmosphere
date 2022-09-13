package phases

import (
	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	v1 "k8s.io/api/core/v1"
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
				Namespace:   "cert-manager",
				ReleaseName: "cert-manager",
				ApiGroup:    "cert-manager.io",
				ChartSpec: helmv2.HelmChartTemplateSpec{
					Chart:     "cert-manager",
					Version:   "v1.7.1",
					SourceRef: CertManagerSourceRef,
				},
				Values: map[string]interface{}{
					"installCRDs": true,
					"volumes": []v1.Volume{
						{
							Name: "etc-ssl-certs",
							VolumeSource: v1.VolumeSource{
								HostPath: &v1.HostPathVolumeSource{
									Path: "/etc/ssl/certs",
								},
							},
						},
					},
					"volumeMounts": []v1.VolumeMount{
						{
							Name:      "etc-ssl-certs",
							ReadOnly:  true,
							MountPath: "/etc/ssl/certs",
						},
					},
					"nodeSelector": ControlPlaneNodeSelector,
					"webhook": map[string]interface{}{
						"nodeSelector": ControlPlaneNodeSelector,
					},
					"cainjector": map[string]interface{}{
						"nodeSelector": ControlPlaneNodeSelector,
					},
					"startupapicheck": map[string]interface{}{
						"nodeSelector": ControlPlaneNodeSelector,
					},
				},
			},
		},
	}
}
