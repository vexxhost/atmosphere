package deployment

import (
	"time"

	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func (d *Deployment) EnsureMemcached() error {
	release := &helmv2.HelmRelease{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "memcached",
			Namespace: "openstack",
		},
		Spec: helmv2.HelmReleaseSpec{
			Chart: helmv2.HelmChartTemplate{
				Spec: helmv2.HelmChartTemplateSpec{
					Chart:             "memcached",
					Version:           "0.1.6",
					ReconcileStrategy: "ChartVersion",
					SourceRef: helmv2.CrossNamespaceObjectReference{
						Kind: "HelmRepository",
						Name: "openstack-helm-infra",
					},
				},
			},
			Interval: metav1.Duration{
				Duration: time.Minute,
			},
			ValuesFrom: []helmv2.ValuesReference{
				{
					Kind:      "Secret",
					Name:      "openstack-helm-config",
					ValuesKey: "endpoints.yml",
					Optional:  false,
				},
				{
					Kind:      "Secret",
					Name:      "openstack-helm-config",
					ValuesKey: "memcached.yml",
					Optional:  false,
				},
				{
					Kind:      "Secret",
					Name:      "openstack-helm-config",
					ValuesKey: "memcached-overrides.yml",
					Optional:  true,
				},
			},
		},
	}

	return d.EnsureHelmRelease(release)
}
