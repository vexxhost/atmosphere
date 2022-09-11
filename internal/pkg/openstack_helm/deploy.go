package openstack_helm

import (
	"context"

	log "github.com/sirupsen/logrus"
	"github.com/vexxhost/atmosphere/internal/pkg/kubernetes"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
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

	return nil
}
