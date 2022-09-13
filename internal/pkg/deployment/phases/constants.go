package phases

import (
	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
)

var ControlPlaneNodeSelector map[string]string = map[string]string{
	"openstack-control-plane": "enabled",
}

var CertManagerSourceRef helmv2.CrossNamespaceObjectReference = helmv2.CrossNamespaceObjectReference{
	Kind:      "HelmRepository",
	Namespace: "cert-manager",
	Name:      "jetstack",
}

var NodeFeatureDiscoverySourceRef helmv2.CrossNamespaceObjectReference = helmv2.CrossNamespaceObjectReference{
	Kind:      "HelmRepository",
	Namespace: "monitoring",
	Name:      "node-feature-discovery",
}

var IngressNginxSourceRef helmv2.CrossNamespaceObjectReference = helmv2.CrossNamespaceObjectReference{
	Kind:      "HelmRepository",
	Namespace: "openstack",
	Name:      "ingress-nginx",
}

var OpenstackHelmInfraSourceRef helmv2.CrossNamespaceObjectReference = helmv2.CrossNamespaceObjectReference{
	Kind:      "HelmRepository",
	Namespace: "openstack",
	Name:      "openstack-helm-infra",
}
