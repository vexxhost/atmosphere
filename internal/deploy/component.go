// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"fmt"
	"slices"
	"sort"
	"strings"

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

// DependencyOptions contains runtime values which affect the component graph.
// Defaults preserve the behavior of a normal production deployment.
type DependencyOptions map[string]string

const (
	DependencyOptionCSIDriver      = "csi_driver"
	DependencyOptionNetworkBackend = "network_backend"
)

// DefaultDependencyOptions returns dependency option defaults matching the
// defaults used by the Ansible roles.
func DefaultDependencyOptions() DependencyOptions {
	return DependencyOptions{
		DependencyOptionCSIDriver:      "rbd",
		DependencyOptionNetworkBackend: "openvswitch",
	}
}

// ValidateDependencyOptions rejects misspelled or unsupported graph options.
func ValidateDependencyOptions(options DependencyOptions) error {
	for key, value := range options {
		if value == "" {
			return fmt.Errorf("dependency option %q must not be empty", key)
		}
		switch key {
		case DependencyOptionCSIDriver:
		case DependencyOptionNetworkBackend:
			if value != "openvswitch" && value != "ovn" {
				return fmt.Errorf("unsupported network backend %q", value)
			}
		default:
			return fmt.Errorf("unknown dependency option %q", key)
		}
	}
	return nil
}

// ConditionalDependency is enabled only when a dependency option has one of
// the configured values.
type ConditionalDependency struct {
	Name   string
	Option string
	Values []string
}

func (d ConditionalDependency) enabled(options DependencyOptions) bool {
	return slices.Contains(d.Values, options[d.Option])
}

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
	// ConditionalDependsOn lists main-role dependencies which vary with
	// deployment configuration, such as the selected CSI driver.
	ConditionalDependsOn []ConditionalDependency
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
	// PreRoleName is an optional Ansible role to run concurrently with the main
	// role. This enables intra-component parallelism: pre-work (e.g., creating
	// OpenStack resources, downloading images) overlaps with the Helm install.
	// Both must complete before the component is considered done.
	PreRoleName string
	// PreRoleDependsOn lists component Names that must complete before the
	// pre-role may start. When empty, the pre-role starts as soon as the
	// component's own DependsOn are satisfied (the current behaviour). When
	// set, the main role still starts eagerly while the pre-role waits.
	// This enables asymmetric gating — e.g. keystone's Keycloak realm
	// creation (pre-role) waits for keycloak while the keystone Helm install
	// (main role) runs in parallel with keycloak startup.
	PreRoleDependsOn []string
	// ConditionalPreRoleDependsOn lists configuration-dependent dependencies
	// which must complete before the pre-role starts.
	ConditionalPreRoleDependsOn []ConditionalDependency
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
		Name:     "ceph",
		Type:     PlaybookType,
		Playbook: "ceph",
		// "apt": ceph installs packages; serialize against other apt
		// consumers to avoid dpkg lock contention.
		// "containerd": both the ceph and kubernetes playbooks include
		// the vexxhost.containers.containerd role, which calls
		// systemctl daemon-reload + enable on containerd.service.
		// When run in parallel, the two enable calls race on dbus and
		// intermittently fail with:
		//   "Unable to enable service containerd: Failed to enable
		//    unit: Message recipient disconnected from message bus
		//    without replying"
		Resources: []string{"apt", "containerd"},
	},
	{
		Name:     "kubernetes",
		Type:     PlaybookType,
		Playbook: "kubernetes",
		// "apt": kubernetes installs apt packages; serialize against
		// other apt consumers to avoid dpkg lock contention.
		// "containerd": shares vexxhost.containers.containerd with the
		// ceph playbook — see ceph above for the dbus race details.
		Resources: []string{"apt", "containerd"},
	},
	{
		Name:      "csi",
		Type:      PlaybookType,
		Playbook:  "csi",
		DependsOn: []string{"kubernetes"},
		ConditionalDependsOn: []ConditionalDependency{
			{
				Name:   "ceph",
				Option: DependencyOptionCSIDriver,
				Values: []string{"rbd"},
			},
		},
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
		// Helm install talks to apiserver; counts toward k8s-api cap to
		// prevent Wave 2 fan-out from overloading a single-node apiserver.
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "rabbitmq-cluster-operator",
		Type:      RoleType,
		RoleName:  "rabbitmq_cluster_operator",
		Hosts:     "controllers",
		DependsOn: []string{"cert-manager"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "percona-xtradb-cluster-operator",
		Type:      RoleType,
		RoleName:  "percona_xtradb_cluster_operator",
		Hosts:     "controllers",
		DependsOn: []string{"cert-manager"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "percona-xtradb-cluster",
		Type:      RoleType,
		RoleName:  "percona_xtradb_cluster",
		Hosts:     "controllers",
		DependsOn: []string{"percona-xtradb-cluster-operator", "csi"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "valkey",
		Type:      RoleType,
		RoleName:  "valkey",
		Hosts:     "controllers",
		DependsOn: []string{"kubernetes", "csi", "cluster-issuer"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "keycloak",
		Type:      RoleType,
		RoleName:  "keycloak",
		Hosts:     "controllers",
		DependsOn: []string{"percona-xtradb-cluster", "ingress-nginx", "cluster-issuer"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "keepalived",
		Type:      RoleType,
		RoleName:  "keepalived",
		Hosts:     "controllers",
		DependsOn: []string{"kubernetes"},
	},

	// Monitoring (RoleType, Hosts: "controllers[0]")
	{
		Name:      "node-feature-discovery",
		Type:      RoleType,
		RoleName:  "node_feature_discovery",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "kube-prometheus-stack",
		Type:      RoleType,
		RoleName:  "kube_prometheus_stack",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes", "csi", "cluster-issuer", "keycloak"},
		Resources: []string{"k8s-api", "keycloak-admin"},
	},
	{
		Name:      "loki",
		Type:      RoleType,
		RoleName:  "loki",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes", "csi"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "vector",
		Type:      RoleType,
		RoleName:  "vector",
		Hosts:     "controllers[0]",
		DependsOn: []string{"loki"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "goldpinger",
		Type:      RoleType,
		RoleName:  "goldpinger",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "ipmi-exporter",
		Type:      RoleType,
		RoleName:  "ipmi_exporter",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kube-prometheus-stack"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "prometheus-pushgateway",
		Type:      RoleType,
		RoleName:  "prometheus_pushgateway",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kube-prometheus-stack"},
		Resources: []string{"k8s-api"},
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
		// Pre-pull all known Atmosphere container images on every node
		// so later component Helm installs do not stall in
		// ImagePulling. Best-effort: failures are non-fatal because
		// the kubelet falls back to on-demand pulls.
		Name:        "image-warmup",
		Type:        RoleType,
		RoleName:    "image_warmup",
		Hosts:       "controllers:computes",
		DependsOn:   []string{"kubernetes"},
		GatherFacts: boolPtr(false),
	},
	{
		Name:      "memcached",
		Type:      RoleType,
		RoleName:  "memcached",
		Hosts:     "controllers[0]",
		DependsOn: []string{"kubernetes"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:             "keystone",
		Type:             RoleType,
		RoleName:         "keystone",
		PreRoleName:      "keystone_pre",
		Hosts:            "controllers[0]",
		DependsOn:        []string{"ingress-nginx", "rabbitmq-cluster-operator", "percona-xtradb-cluster", "memcached"},
		PreRoleDependsOn: []string{"keycloak"},
		Resources:        []string{"k8s-api", "keycloak-admin"},
	},
	{
		Name:      "barbican",
		Type:      RoleType,
		RoleName:  "barbican",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:        "rook-ceph",
		Type:        RoleType,
		RoleName:    "rook_ceph",
		Hosts:       "controllers[0]",
		DependsOn:   []string{"kubernetes"},
		Environment: cephEnvironment,
		Resources:   []string{"k8s-api"},
	},
	{
		Name:        "rook-ceph-cluster",
		Type:        RoleType,
		RoleName:    "rook_ceph_cluster",
		Hosts:       "controllers[0]",
		DependsOn:   []string{"rook-ceph", "ceph", "keystone"},
		Environment: cephEnvironment,
		Resources:   []string{"k8s-api"},
	},
	{
		Name:        "ceph-provisioners",
		Type:        RoleType,
		RoleName:    "ceph_provisioners",
		Hosts:       "controllers[0]",
		DependsOn:   []string{"ceph", "kubernetes"},
		Environment: cephEnvironment,
		Resources:   []string{"k8s-api"},
	},
	{
		Name:      "glance",
		Type:      RoleType,
		RoleName:  "glance",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone", "ceph-provisioners"},
		Resources: []string{"k8s-api"},
	},
	{
		// Image uploads run as a separate component so they do not block
		// downstream services (Nova, Magnum, etc.) which only need the
		// Glance API to be deployed.
		Name:      "glance-images",
		Type:      RoleType,
		RoleName:  "glance_images",
		Hosts:     "controllers[0]",
		DependsOn: []string{"glance"},
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
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "placement",
		Type:      RoleType,
		RoleName:  "placement",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone"},
		Resources: []string{"k8s-api"},
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
		Resources: []string{"k8s-api"},
	},
	{
		// The pre-role does the Helm install (heavy, ~5 min) and only
		// requires Keystone and the configured network backend. The main
		// role's only remaining
		// work is the post-install "Create networks" task, which hits
		// neutron-server's AZ check that needs Nova compute to have
		// registered the default availability zone "nova". Splitting
		// the role lets the install overlap with Nova while the cheap
		// network creation continues to wait on Nova.
		Name:             "neutron",
		Type:             RoleType,
		RoleName:         "neutron",
		PreRoleName:      "neutron_pre",
		Hosts:            "controllers[0]",
		DependsOn:        []string{"nova"},
		PreRoleDependsOn: []string{"keystone", "openvswitch"},
		ConditionalPreRoleDependsOn: []ConditionalDependency{
			{
				Name:   "coredns",
				Option: DependencyOptionNetworkBackend,
				Values: []string{"openvswitch"},
			},
			{
				Name:   "ovn",
				Option: DependencyOptionNetworkBackend,
				Values: []string{"ovn"},
			},
		},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "heat",
		Type:      RoleType,
		RoleName:  "heat",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:        "octavia",
		Type:        RoleType,
		RoleName:    "octavia",
		PreRoleName: "octavia_pre",
		Hosts:       "controllers[0]",
		DependsOn:   []string{"keystone", "nova", "neutron"},
		Resources:   []string{"k8s-api"},
	},
	{
		Name:             "magnum",
		Type:             RoleType,
		RoleName:         "magnum",
		PreRoleName:      "magnum_pre",
		Hosts:            "controllers[0]",
		DependsOn:        []string{"keystone", "glance"},
		PreRoleDependsOn: []string{"glance-images"},
		Resources:        []string{"k8s-api"},
	},
	{
		Name:      "manila",
		Type:      RoleType,
		RoleName:  "manila",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone", "nova", "neutron", "cinder"},
		Resources: []string{"k8s-api"},
	},
	{
		Name:      "horizon",
		Type:      RoleType,
		RoleName:  "horizon",
		Hosts:     "controllers[0]",
		DependsOn: []string{"keystone"},
		Resources: []string{"k8s-api"},
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
	return BuildGraphWithOptions(nil)
}

// BuildGraphWithOptions constructs a DAG using configuration-dependent
// component relationships.
func BuildGraphWithOptions(options DependencyOptions) (*dag.Graph[Component], error) {
	if err := ValidateDependencyOptions(options); err != nil {
		return nil, err
	}
	options = dependencyOptionsWithDefaults(options)

	g := dag.NewGraph[Component]()
	for _, c := range Components {
		if err := g.AddNode(c.Name, c); err != nil {
			return nil, fmt.Errorf("adding node %s: %w", c.Name, err)
		}
	}
	for _, c := range Components {
		for _, dep := range mainDependencies(c, options) {
			if err := g.AddEdge(c.Name, dep); err != nil {
				return nil, fmt.Errorf("adding edge %s -> %s: %w", c.Name, dep, err)
			}
		}
	}
	return g, nil
}

// BootstrapComponentNames returns the requested components and every
// transitive dependency required to deploy them in a fresh environment.
// Pre-role dependencies are included because, unlike normal --tags behavior,
// a fresh environment cannot assume that they are already available.
func BootstrapComponentNames(targets []string, options DependencyOptions) ([]string, error) {
	if err := ValidateDependencyOptions(options); err != nil {
		return nil, err
	}
	options = dependencyOptionsWithDefaults(options)

	registry := make(map[string]Component, len(Components))
	for _, component := range Components {
		registry[component.Name] = component
	}

	const (
		unvisited = iota
		visiting
		visited
	)
	state := make(map[string]int, len(Components))
	selected := make(map[string]bool, len(Components))
	var stack []string

	var visit func(string) error
	visit = func(name string) error {
		component, ok := registry[name]
		if !ok {
			return fmt.Errorf("component %q not found", name)
		}

		switch state[name] {
		case visiting:
			cycleStart := slices.Index(stack, name)
			cycle := append(slices.Clone(stack[cycleStart:]), name)
			return fmt.Errorf("dependency cycle detected: %s", strings.Join(cycle, " -> "))
		case visited:
			return nil
		}

		state[name] = visiting
		stack = append(stack, name)
		for _, dependency := range bootstrapDependencies(component, options) {
			if err := visit(dependency); err != nil {
				return err
			}
		}
		stack = stack[:len(stack)-1]
		state[name] = visited
		selected[name] = true
		return nil
	}

	for _, target := range targets {
		if err := visit(target); err != nil {
			return nil, err
		}
	}

	names := make([]string, 0, len(selected))
	for name := range selected {
		names = append(names, name)
	}
	sort.Strings(names)
	return names, nil
}

func dependencyOptionsWithDefaults(options DependencyOptions) DependencyOptions {
	resolved := DefaultDependencyOptions()
	for key, value := range options {
		resolved[key] = value
	}
	return resolved
}

func mainDependencies(component Component, options DependencyOptions) []string {
	dependencies := slices.Clone(component.DependsOn)
	for _, dependency := range component.ConditionalDependsOn {
		if dependency.enabled(options) {
			dependencies = append(dependencies, dependency.Name)
		}
	}
	return dependencies
}

func preRoleDependencies(component Component, options DependencyOptions) []string {
	dependencies := slices.Clone(component.PreRoleDependsOn)
	for _, dependency := range component.ConditionalPreRoleDependsOn {
		if dependency.enabled(options) {
			dependencies = append(dependencies, dependency.Name)
		}
	}
	return dependencies
}

func bootstrapDependencies(component Component, options DependencyOptions) []string {
	return append(
		mainDependencies(component, options),
		preRoleDependencies(component, options)...,
	)
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
