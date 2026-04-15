package deploy

import (
	"fmt"

	"github.com/vexxhost/atmosphere/pkg/dag"
)

// ComponentType distinguishes between full-playbook and single-role components.
type ComponentType int

const (
	// RoleType: single Ansible role → generates a minimal playbook at runtime
	RoleType ComponentType = iota
	// PlaybookType: full multi-play playbook → runs the file directly
	PlaybookType
)

// Component represents a deployable unit in the Atmosphere platform.
type Component struct {
	// Name is the unique identifier (kebab-case), e.g., "cert-manager"
	Name string
	// Type is RoleType or PlaybookType
	Type ComponentType
	// Tag is the Ansible tag (if different from Name). Empty means use Name.
	Tag string
	// Playbook is the playbook filename (without .yml) for PlaybookType, e.g., "ceph"
	Playbook string
	// RoleName is the Ansible role name for RoleType, e.g., "cert_manager"
	RoleName string
	// Hosts is the Ansible host pattern, e.g., "controllers[0]", "controllers:computes"
	Hosts string
	// DependsOn lists component Names that must complete before this one
	DependsOn []string
	// When is an optional Ansible conditional expression
	When string
	// Environment contains optional play-level environment variables
	Environment map[string]string
	// GatherFacts controls fact gathering. nil = default (true), ptr to false = skip
	GatherFacts *bool
	// Resources lists named resources this component requires exclusive access to.
	// Components sharing a resource are serialized even if the DAG allows parallelism.
	// Example: []string{"apt"} serializes all components that use package management.
	Resources []string
}

// EffectiveTag returns the Ansible tag for this component.
func (c Component) EffectiveTag() string {
	if c.Tag != "" {
		return c.Tag
	}
	return c.Name
}

// boolPtr returns a pointer to a bool value.
func boolPtr(b bool) *bool {
	return &b
}

var cephEnvironment = map[string]string{
	"CEPH_CONTAINER_IMAGE":  `{{ cephadm_image | default('quay.io/ceph/ceph:v' + (ceph_version | default('18.2.7'))) }}`,
	"CEPH_CONTAINER_BINARY": "docker",
}

// Components is the full registry of all deployment components.
var Components = []Component{
	// Foundation (PlaybookType)
	{
		Name:      "ceph",
		Type:      PlaybookType,
		Playbook:  "ceph",
		Resources: []string{"apt"},
	},
	{
		Name:      "kubernetes",
		Type:      PlaybookType,
		Playbook:  "kubernetes",
		Resources: []string{"apt"},
	},
	{
		Name:      "csi",
		Type:      PlaybookType,
		Playbook:  "csi",
		DependsOn: []string{"ceph", "kubernetes"},
	},

	// Pre-download (upload charts and pull images early to avoid per-component overhead)
	{
		Name:      "upload-charts",
		Type:      RoleType,
		RoleName:  "upload_helm_charts",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes"},
	},
	{
		Name:      "prepull-images",
		Type:      RoleType,
		RoleName:  "prepull_images",
		Hosts:     "controllers:computes",
		DependsOn: []string{"kubernetes"},
	},

	// Infrastructure (RoleType, Hosts: "controllers")
	{
		Name:      "cert-manager",
		Type:      RoleType,
		RoleName:  "cert_manager",
		Hosts:     "controllers",
		DependsOn: []string{"kubernetes"},
	},
	{
		Name:      "cluster-issuer",
		Type:      RoleType,
		RoleName:  "cluster_issuer",
		Hosts:     "controllers",
		DependsOn: []string{"cert-manager"},
	},
	{
		Name:      "ingress-nginx",
		Type:      RoleType,
		RoleName:  "ingress_nginx",
		Hosts:     "controllers",
		DependsOn: []string{"kubernetes"},
	},
	{
		Name:      "rabbitmq-cluster-operator",
		Type:      RoleType,
		RoleName:  "rabbitmq_cluster_operator",
		Hosts:     "controllers",
		DependsOn: []string{"cert-manager"},
	},
	{
		Name:      "percona-xtradb-cluster-operator",
		Type:      RoleType,
		RoleName:  "percona_xtradb_cluster_operator",
		Hosts:     "controllers",
		DependsOn: []string{"cert-manager"},
	},
	{
		Name:      "percona-xtradb-cluster",
		Type:      RoleType,
		RoleName:  "percona_xtradb_cluster",
		Hosts:     "controllers",
		DependsOn: []string{"percona-xtradb-cluster-operator", "csi", "memcached"},
	},
	{
		Name:      "valkey",
		Type:      RoleType,
		RoleName:  "valkey",
		Hosts:     "controllers",
		DependsOn: []string{"kubernetes", "csi", "cluster-issuer"},
	},
	{
		Name:      "keycloak",
		Type:      RoleType,
		RoleName:  "keycloak",
		Hosts:     "controllers",
		DependsOn: []string{"percona-xtradb-cluster", "ingress-nginx", "valkey"},
	},
	{
		Name:      "keepalived",
		Type:      RoleType,
		RoleName:  "keepalived",
		Hosts:     "controllers",
		DependsOn: []string{"memcached"},
	},

	// Monitoring (RoleType, Hosts: "controllers[0]")
	{
		Name:      "node-feature-discovery",
		Type:      RoleType,
		RoleName:  "node_feature_discovery",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes"},
	},
	{
		Name:      "kube-prometheus-stack",
		Type:      RoleType,
		RoleName:  "kube_prometheus_stack",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes", "csi", "cluster-issuer", "keycloak"},
	},
	{
		Name:      "loki",
		Type:      RoleType,
		RoleName:  "loki",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes", "csi"},
	},
	{
		Name:      "vector",
		Type:      RoleType,
		RoleName:  "vector",
		Hosts:     "controllers[0]",
		DependsOn: []string{"loki"},
	},
	{
		Name:      "goldpinger",
		Type:      RoleType,
		RoleName:  "goldpinger",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes"},
	},
	{
		Name:      "ipmi-exporter",
		Type:      RoleType,
		RoleName:  "ipmi_exporter",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kube-prometheus-stack"},
	},
	{
		Name:      "prometheus-pushgateway",
		Type:      RoleType,
		RoleName:  "prometheus_pushgateway",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kube-prometheus-stack"},
	},

	// OS Configuration (RoleType, Hosts: "controllers:computes")
	// These are pure host config — no K8s dependency.
	{
		Name:     "lpfc",
		Type:     RoleType,
		RoleName: "lpfc",
		Hosts:    "controllers:computes",
	},
	{
		Name:      "multipathd",
		Type:      RoleType,
		RoleName:  "multipathd",
		Hosts:     "controllers:computes",
		Resources: []string{"apt"},
	},
	{
		Name:      "iscsi",
		Type:      RoleType,
		RoleName:  "iscsi",
		Hosts:     "controllers:computes",
		Resources: []string{"apt"},
	},
	{
		Name:     "udev",
		Type:     RoleType,
		RoleName: "udev",
		Hosts:    "controllers:computes",
	},

	// OpenStack (RoleType, Hosts: "controllers[0]")
	{
		Name:      "memcached",
		Type:      RoleType,
		RoleName:  "memcached",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes"},
	},
	{
		Name:      "keystone",
		Type:      RoleType,
		RoleName:  "keystone",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keycloak", "ingress-nginx", "rabbitmq-cluster-operator", "percona-xtradb-cluster", "memcached"},
	},
	{
		Name:      "barbican",
		Type:      RoleType,
		RoleName:  "barbican",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone"},
	},
	{
		Name:        "rook-ceph",
		Type:        RoleType,
		RoleName:    "rook_ceph",
		Hosts:       "controllers[0]",
		DependsOn:   []string{"kubernetes"},
		Environment: cephEnvironment,
	},
	{
		Name:        "rook-ceph-cluster",
		Type:        RoleType,
		RoleName:    "rook_ceph_cluster",
		Hosts:       "controllers[0]",
		DependsOn:   []string{"rook-ceph", "ceph", "barbican"},
		Environment: cephEnvironment,
	},
	{
		Name:        "ceph-provisioners",
		Type:        RoleType,
		RoleName:    "ceph_provisioners",
		Hosts:       "controllers[0]",
		DependsOn:   []string{"ceph"},
		Environment: cephEnvironment,
	},
	{
		Name:      "glance",
		Type:      RoleType,
		RoleName:  "glance",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone"},
	},
	{
		Name:      "staffeln",
		Type:      RoleType,
		RoleName:  "staffeln",
		Hosts:     "controllers[0]",
		DependsOn: []string{"cinder"},
		When:      `atmosphere_staffeln_enabled | default(true)`,
	},
	{
		Name:      "cinder",
		Type:      RoleType,
		RoleName:  "cinder",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone", "ceph-provisioners"},
	},
	{
		Name:      "placement",
		Type:      RoleType,
		RoleName:  "placement",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone"},
	},

	// SDN (RoleType, Hosts: "controllers:computes", GatherFacts: false)
	{
		Name:        "openvswitch",
		Type:        RoleType,
		RoleName:    "openvswitch",
		Hosts:       "controllers:computes",
		DependsOn:   []string{"kubernetes"},
		GatherFacts: boolPtr(false),
	},
	{
		Name:        "frr-k8s",
		Type:        RoleType,
		RoleName:    "frr_k8s",
		Tag:         "frr_k8s",
		Hosts:       "controllers:computes",
		DependsOn:   []string{"kubernetes"},
		When:        `ovn_bgp_agent_enabled | default(false)`,
		GatherFacts: boolPtr(false),
	},
	{
		Name:        "ovn",
		Type:        RoleType,
		RoleName:    "ovn",
		Hosts:       "controllers:computes",
		DependsOn:   []string{"openvswitch"},
		GatherFacts: boolPtr(false),
	},

	// Remaining OpenStack (RoleType, Hosts: "controllers[0]")
	{
		Name:      "libvirt",
		Type:      RoleType,
		RoleName:  "libvirt",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes", "cluster-issuer"},
	},
	{
		Name:      "coredns",
		Type:      RoleType,
		RoleName:  "coredns",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes"},
	},
	{
		Name:      "nova",
		Type:      RoleType,
		RoleName:  "nova",
		Hosts:     "controllers[0]",
		DependsOn: []string{"placement", "glance", "libvirt"},
	},
	{
		Name:      "neutron",
		Type:      RoleType,
		RoleName:  "neutron",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone", "nova", "ovn", "coredns"},
	},
	{
		Name:      "heat",
		Type:      RoleType,
		RoleName:  "heat",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone"},
	},
	{
		Name:      "octavia",
		Type:      RoleType,
		RoleName:  "octavia",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone", "nova", "neutron"},
	},
	{
		Name:      "magnum",
		Type:      RoleType,
		RoleName:  "magnum",
		Hosts:     "controllers[0]",
		DependsOn: []string{"octavia", "barbican", "heat"},
	},
	{
		Name:      "manila",
		Type:      RoleType,
		RoleName:  "manila",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone", "nova", "neutron", "cinder"},
	},
	{
		Name:      "horizon",
		Type:      RoleType,
		RoleName:  "horizon",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone"},
	},
	{
		Name:      "openstack-exporter",
		Type:      RoleType,
		RoleName:  "openstack_exporter",
		Hosts:     "controllers[0]",
		DependsOn: []string{"cinder", "neutron"},
	},
	{
		Name:      "openstack-cli",
		Type:      RoleType,
		RoleName:  "openstack_cli",
		Hosts:     "controllers",
		DependsOn: []string{"keystone"},
	},
}

// BuildGraph constructs a DAG from the component registry.
func BuildGraph() (*dag.Graph[Component], error) {
	g := dag.NewGraph[Component]()
	for _, c := range Components {
		g.AddNode(c.Name, c)
	}
	for _, c := range Components {
		for _, dep := range c.DependsOn {
			if err := g.AddEdge(c.Name, dep); err != nil {
				return nil, fmt.Errorf("adding edge %s -> %s: %w", c.Name, dep, err)
			}
		}
	}
	return g, nil
}

// FindComponent looks up a component by name or tag.
func FindComponent(nameOrTag string) (Component, bool) {
	for _, c := range Components {
		if c.Name == nameOrTag || c.EffectiveTag() == nameOrTag {
			return c, true
		}
	}
	return Component{}, false
}
