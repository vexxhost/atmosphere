package openstack_helm

import (
	"context"
	"fmt"
	"time"

	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	log "github.com/sirupsen/logrus"
	"github.com/vexxhost/atmosphere/internal/pkg/kubernetes"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func Deploy(ctx context.Context) error {
	log.Info("📃 Building configuration values")

	secret, err := GetConfigSecret()
	if err != nil {
		return err
	}

	clientset, err := kubernetes.GetClientSet()
	if err != nil {
		return err
	}

	_, err = clientset.CoreV1().Secrets("openstack").Apply(ctx, secret, metav1.ApplyOptions{
		FieldManager: "atmosphere",
	})
	if err != nil {
		return err
	}

	log.Info("🚀 Deployed configuration values")

	// TODO: deploy helm repos
	kubeClient, err := kubernetes.GetClient()
	if err != nil {
		return err
	}

	for _, svc := range SERVICES {
		release := &helmv2.HelmRelease{
			ObjectMeta: metav1.ObjectMeta{
				Name:      svc,
				Namespace: "openstack",
			},
		}
		err := kubeClient.Get(ctx, client.ObjectKey{Name: svc, Namespace: "openstack"}, release)

		release.Spec = helmv2.HelmReleaseSpec{
			Chart: helmv2.HelmChartTemplate{
				Spec: helmv2.HelmChartTemplateSpec{
					Chart:             svc,
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
					ValuesKey: fmt.Sprintf("%s.yml", svc),
					Optional:  false,
				},
				{
					Kind:      "Secret",
					Name:      "openstack-helm-config",
					ValuesKey: fmt.Sprintf("%s-overrides.yml", svc),
					Optional:  true,
				},
			},
		}

		// TODO: if failed to grab release, fail.
		if false {
			return err
		}

		// TODO: if not count, create
		if false {
			err = kubeClient.Create(ctx, release)
			if err != nil {
				return err
			}
		} else {
			err = kubeClient.Update(ctx, release)
			if err != nil {
				return err
			}
		}

		// TODO: otherwise update the release

		// err = kubeClient.Create(ctx, &release)
		if err != nil {
			return err
		}

		log.WithFields(log.Fields{
			"chart": svc,
		}).Info("🚀 Deployed HelmRelease")
	}

	return nil
}
