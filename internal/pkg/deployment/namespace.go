package deployment

import (
	log "github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func (d *Deployment) EnsureNamespace() error {
	log := log.WithField("namespace", "openstack")
	namespace := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: "openstack",
		},
	}

	err := d.client.Get(d.context, client.ObjectKey{Name: "openstack"}, namespace)
	if client.IgnoreNotFound(err) != nil {
		return err
	}

	if errors.IsNotFound(err) {
		if err := d.client.Create(d.context, namespace); err != nil {
			return err
		}
		log.Info("🚀 Namespace created")
	} else {
		log.Info("🚀 Namespace already exists")
	}

	return nil
}
