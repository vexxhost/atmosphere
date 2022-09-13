package image_repositories

import (
	"fmt"
	"strings"
)

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
	"designate":     "bind9utils",
	"glance":        "kubectl lsscsi nvme-cli sysfsutils udev util-linux",
	"heat":          "curl",
	"ironic":        "ethtool lshw iproute2",
	"monasca-agent": "iproute2 libvirt-clients lshw",
	"neutron":       "jq ethtool lshw",
	"nova":          "ovmf qemu-efi-aarch64",
}
var PIP_PACKAGES map[string]string = map[string]string{
	"glance":        "glance_store[cinder]",
	"horizon":       "designate-dashboard heat-dashboard ironic-ui magnum-ui neutron-vpnaas-dashboard octavia-dashboard senlin-dashboard monasca-ui",
	"ironic":        "python-dracclient sushy",
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

	pipPackages := ""
	if val, ok := PIP_PACKAGES[project]; ok {
		pipPackages = val
	}

	platforms := "linux/amd64"
	if val, ok := PLATFORMS[project]; ok {
		platforms = val
	}

	buildArgs := []string{
		"RELEASE=${{ matrix.release }}",
		fmt.Sprintf("PROJECT=%s", project),
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
					Matrix: map[string][]string{
						"release": {"wallaby", "xena", "yoga"},
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
							"cache-from": "type=gha,scope=${{ matrix.release }}",
							"cache-to":   "type=gha,mode=max,scope=${{ matrix.release }}",
							"platforms":  platforms,
							"push":       "${{ github.event_name == 'push' }}",
							"build-args": strings.Join(buildArgs, "\n"),
							"tags":       fmt.Sprintf("quay.io/vexxhost/%s:${{ env.PROJECT_REF }}", project),
						},
					},
					{
						Name: "Promote image",
						Uses: "akhilerm/tag-push-action@v2.0.0",
						If:   "github.ref == 'refs/heads/main'",
						With: map[string]string{
							"src": fmt.Sprintf("quay.io/vexxhost/%s:${{ env.PROJECT_REF }}", project),
							"dst": fmt.Sprintf("quay.io/vexxhost/%s:${{ matrix.release }}", project),
						},
					},
				},
			},
		},
	}
}
