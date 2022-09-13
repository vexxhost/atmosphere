package phases

import (
	helmv2 "github.com/fluxcd/helm-controller/api/v2beta1"
)

var ControlPlaneNodeSelector map[string]string = map[string]string{
	"openstack-control-plane": "enabled",
}

var NodeFeatureDiscoverySourceRef helmv2.CrossNamespaceObjectReference = helmv2.CrossNamespaceObjectReference{
	Kind:      "HelmRepository",
	Namespace: "monitoring",
	Name:      "node-feature-discovery",
}

var OpenstackHelmInfraSourceRef helmv2.CrossNamespaceObjectReference = helmv2.CrossNamespaceObjectReference{
	Kind:      "HelmRepository",
	Namespace: "openstack",
	Name:      "openstack-helm-infra",
}
