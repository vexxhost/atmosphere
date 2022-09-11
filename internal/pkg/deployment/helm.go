package deployment

import (
	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
	log "github.com/sirupsen/logrus"
	"k8s.io/apimachinery/pkg/api/errors"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func (d *Deployment) EnsureHelmRelease(release *helmv2.HelmRelease) error {
	log := log.WithField("release", release.Name)
	deployedRelease := &helmv2.HelmRelease{
		ObjectMeta: release.ObjectMeta,
	}

	err := d.client.Get(d.context, client.ObjectKey{Name: release.Name, Namespace: release.Namespace}, deployedRelease)
	if client.IgnoreNotFound(err) != nil {
		return err
	}

	if errors.IsNotFound(err) {
		if err := d.client.Create(d.context, release); err != nil {
			return err
		}

		log.Info("🚀 Helm release created")
	} else {
		deployedRelease.Spec = release.Spec
		if err := d.client.Update(d.context, deployedRelease); err != nil {
			return err
		}

		log.Info("🚀 Helm release updated")
	}

	return nil
}
