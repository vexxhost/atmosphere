package deployment

import (
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"

	"github.com/vexxhost/atmosphere/internal/pkg/kubernetes"
)

func (d *Deployment) CreateNamespace() error {
	c, err := kubernetes.GetClient()
	if err != nil {
		return err
	}

	namespace := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: "openstack",
		},
	}

	err = c.Get(d.context, client.ObjectKey{Name: "openstack"}, namespace)
	if client.IgnoreNotFound(err) != nil {
		return err
	}

	if errors.IsNotFound(err) {
		return c.Create(d.context, namespace)
	}

	return c.Update(d.context, namespace)
}
