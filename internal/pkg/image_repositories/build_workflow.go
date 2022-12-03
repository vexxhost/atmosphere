package image_repositories

import (
	"fmt"
	"strings"
)

var FORKED_PROJECTS map[string]bool = map[string]bool{
	"keystone": true,
}
var EXTRAS map[string]string = map[string]string{}
var PROFILES map[string]string = map[string]string{
	"cinder":            "ceph qemu",
	"glance":            "ceph",
	"horizon":           "apache",
	"ironic":            "ipxe ipmi qemu tftp",
	"keystone":          "apache ldap openidc",
	"monasca-api":       "apache influxdb",
	"monasca-persister": "influxdb",
	"neutron":           "openvswitch vpn",
	"nova":              "ceph openvswitch configdrive qemu migration",
	"placement":         "apache",
}
var DIST_PACAKGES map[string]string = map[string]string{
	"cinder":        "kubectl lsscsi nvme-cli sysfsutils udev util-linux",
	"designate":     "bind9utils",
	"glance":        "kubectl lsscsi nvme-cli sysfsutils udev util-linux",
	"heat":          "curl",
	"ironic":        "ethtool lshw iproute2",
	"monasca-agent": "iproute2 libvirt-clients lshw",
	"neutron":       "jq ethtool lshw",
	"nova":          "ovmf qemu-efi-aarch64 lsscsi nvme-cli sysfsutils udev util-linux ndctl",
}
var PIP_PACKAGES map[string]string = map[string]string{
	"glance":        "glance_store[cinder]",
	"horizon":       "git+https://github.com/openstack/designate-dashboard.git@stable/${{ matrix.release }} git+https://github.com/openstack/heat-dashboard.git@stable/${{ matrix.release }} git+https://github.com/openstack/ironic-ui.git@stable/${{ matrix.release }} git+https://github.com/openstack/magnum-ui.git@stable/${{ matrix.release }} git+https://github.com/openstack/neutron-vpnaas-dashboard.git@stable/${{ matrix.release }} git+https://github.com/openstack/octavia-dashboard.git@stable/${{ matrix.release }} git+https://github.com/openstack/senlin-dashboard.git@stable/${{ matrix.release }} git+https://github.com/openstack/monasca-ui.git@stable/${{ matrix.release }}",
	"ironic":        "python-dracclient sushy",
	"magnum":        "magnum-cluster-api==0.1.2",
	"monasca-agent": "libvirt-python python-glanceclient python-neutronclient python-novaclient py3nvml",
	"neutron":       "neutron-vpnaas",
	"placement":     "httplib2",
}
var PLATFORMS map[string]string = map[string]string{
	"nova":    "linux/amd64,linux/arm64",
	"neutron": "linux/amd64,linux/arm64",
}

func NewBuildWorkflow(project string) *GithubWorkflow {
	extras := ""
	if val, ok := EXTRAS[project]; ok {
		extras = fmt.Sprintf("[%s]", val)
	}

	profiles := ""
	if val, ok := PROFILES[project]; ok {
		profiles = val
	}

	distPackages := ""
	if val, ok := DIST_PACAKGES[project]; ok {
		distPackages = val
	}

	pipPackages := "cryptography"
	if val, ok := PIP_PACKAGES[project]; ok {
		pipPackages += fmt.Sprintf(" %s", val)
	}

	platforms := "linux/amd64"
	if val, ok := PLATFORMS[project]; ok {
		platforms = val
	}

	gitRepo := fmt.Sprintf("https://github.com/openstack/%s", project)
	if _, ok := FORKED_PROJECTS[project]; ok {
		gitRepo = fmt.Sprintf("https://github.com/vexxhost/%s", project)
	}

	buildArgs := []string{
		"RUNTIME_IMAGE=quay.io/vexxhost/openstack-runtime-${{ matrix.from }}",
		"RELEASE=${{ matrix.release }}",
		fmt.Sprintf("PROJECT=%s", project),
		fmt.Sprintf("PROJECT_REPO=%s", gitRepo),
		"PROJECT_REF=${{ env.PROJECT_REF }}",
		fmt.Sprintf("EXTRAS=%s", extras),
		fmt.Sprintf("PROFILES=%s", profiles),
		fmt.Sprintf("DIST_PACKAGES=%s", distPackages),
		fmt.Sprintf("PIP_PACKAGES=%s", pipPackages),
	}

	return &GithubWorkflow{
		Name: "build",
		Concurrency: GithubWorkflowConcurrency{
			Group:            "${{ github.head_ref || github.run_id }}",
			CancelInProgress: true,
		},
		On: GithubWorkflowTrigger{
			PullRequest: GithubWorkflowPullRequest{
				Types: []string{"opened", "synchronize", "reopened"},
			},
			Push: GithubWorkflowPush{
				Branches: []string{"main"},
			},
		},
		Jobs: map[string]GithubWorkflowJob{
			"image": {
				RunsOn: "ubuntu-latest",
				Strategy: GithubWorkflowStrategy{
					Matrix: map[string]interface{}{
						"from":    []string{"focal", "jammy"},
						"release": []string{"wallaby", "xena", "yoga", "zed"},
						"exclude": []map[string]string{
							{
								"from":    "focal",
								"release": "zed",
							},
							{
								"from":    "jammy",
								"release": "wallaby",
							},
							{
								"from":    "jammy",
								"release": "xena",
							},
						},
					},
				},
				Steps: []GithubWorkflowStep{
					{
						Name: "Install QEMU static binaries",
						Uses: "docker/setup-qemu-action@v2",
					},
					{
						Name: "Configure Buildkit",
						Uses: "docker/setup-buildx-action@v2",
					},
					{
						Name: "Checkout project",
						Uses: "actions/checkout@v3",
					},
					{
						Name: "Setup environment variables",
						Run:  "echo PROJECT_REF=$(cat manifest.yml | yq \".${{ matrix.release }}.sha\") >> $GITHUB_ENV",
					},
					{
						Name: "Authenticate with Quay.io",
						Uses: "docker/login-action@v2",
						If:   "${{ github.event_name == 'push' }}",
						With: map[string]string{
							"registry": "quay.io",
							"username": "${{ secrets.QUAY_USERNAME }}",
							"password": "${{ secrets.QUAY_ROBOT_TOKEN }}",
						},
					},
					{
						Name: "Build image",
						Uses: "docker/build-push-action@v3",
						With: map[string]string{
							"context":    ".",
							"cache-from": "type=gha,scope=${{ matrix.from }}-${{ matrix.release }}",
							"cache-to":   "type=gha,mode=max,scope=${{ matrix.from }}-${{ matrix.release }}",
							"platforms":  platforms,
							"push":       "${{ github.event_name == 'push' }}",
							"build-args": strings.Join(buildArgs, "\n"),
							"tags":       fmt.Sprintf("quay.io/vexxhost/%s:${{ env.PROJECT_REF }}-${{ matrix.from }}", project),
						},
					},
					{
						Name: "Promote image",
						Uses: "akhilerm/tag-push-action@v2.0.0",
						If: `
							github.event_name == 'push' && (
							(matrix.from == 'focal') ||
							(matrix.from == 'jammy' && matrix.release != 'yoga')
						)`,
						With: map[string]string{
							"src": fmt.Sprintf("quay.io/vexxhost/%s:${{ env.PROJECT_REF }}-${{ matrix.from }}", project),
							"dst": fmt.Sprintf("quay.io/vexxhost/%s:${{ matrix.release }}", project),
						},
					},
				},
			},
		},
	}
}
