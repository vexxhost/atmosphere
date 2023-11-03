package image_repositories

import (
	"context"
	"fmt"
	"strings"
)

var FORKED_PROJECTS map[string]bool = map[string]bool{
	"horizon":   true,
	"keystone":  true,
	"magnum-ui": true,
	"magnum":    true,
	"manila":    true,
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
	"magnum":        "haproxy",
	"manila":        "iproute2 openvswitch-switch",
	"monasca-agent": "iproute2 libvirt-clients lshw",
	"neutron":       "jq ethtool lshw",
	"nova":          "ovmf qemu-efi-aarch64 lsscsi nvme-cli sysfsutils udev util-linux ndctl",
}
var PIP_PACKAGES map[string][]string = map[string][]string{
	"cinder":        {"purestorage"},
	"glance":        {"glance_store[cinder]"},
	"horizon":       {"git+https://github.com/openstack/designate-dashboard.git@stable/${{ matrix.release }}", "git+https://github.com/openstack/heat-dashboard.git@stable/${{ matrix.release }}", "git+https://github.com/openstack/ironic-ui.git@stable/${{ matrix.release }}", "git+https://github.com/vexxhost/magnum-ui.git@stable/${{ matrix.release }} git+https://github.com/openstack/neutron-vpnaas-dashboard.git@stable/${{ matrix.release }} git+https://github.com/openstack/octavia-dashboard.git@stable/${{ matrix.release }} git+https://github.com/openstack/senlin-dashboard.git@stable/${{ matrix.release }}", "git+https://github.com/openstack/monasca-ui.git@stable/${{ matrix.release }}", "git+https://github.com/openstack/manila-ui.git@stable/${{ matrix.release }}"},
	"ironic":        {"python-dracclient", "sushy"},
	"keystone":      {"keystone-keycloak-backend==0.1.6"},
	"magnum":        {"magnum-cluster-api==0.6.0"},
	"monasca-agent": {"libvirt-python", "python-glanceclient", "python-neutronclient", "python-novaclient", "py3nvml"},
	"neutron":       {"neutron-vpnaas"},
	"octavia":       {"ovn-octavia-provider"},
	"placement":     {"httplib2"},
}
var PLATFORMS map[string]string = map[string]string{
	"nova":    "linux/amd64,linux/arm64",
	"neutron": "linux/amd64,linux/arm64",
}

type ImageBuildArgs struct {
	BuilderImage string
	RuntimeImage string
	Release      string
	Project      string
	ProjectRepo  string
	ProjectRef   string
	Extras       string
	Profiles     string
	DistPackages string
	PipPackages  []string
}

func (args *ImageBuildArgs) DeepCopy() *ImageBuildArgs {
	return &ImageBuildArgs{
		BuilderImage: args.BuilderImage,
		RuntimeImage: args.RuntimeImage,
		Release:      args.Release,
		Project:      args.Project,
		ProjectRepo:  args.ProjectRepo,
		ProjectRef:   args.ProjectRef,
		Extras:       args.Extras,
		Profiles:     args.Profiles,
		DistPackages: args.DistPackages,
		PipPackages:  args.PipPackages,
	}
}

func (args *ImageBuildArgs) ToBuildArgs() []string {
	return []string{
		fmt.Sprintf("BUILDER_IMAGE=%s", args.BuilderImage),
		fmt.Sprintf("RUNTIME_IMAGE=%s", args.RuntimeImage),
		fmt.Sprintf("RELEASE=%s", args.Release),
		fmt.Sprintf("PROJECT=%s", args.Project),
		fmt.Sprintf("PROJECT_REPO=%s", args.ProjectRepo),
		fmt.Sprintf("PROJECT_REF=%s", args.ProjectRef),
		fmt.Sprintf("EXTRAS=%s", args.Extras),
		fmt.Sprintf("PROFILES=%s", args.Profiles),
		fmt.Sprintf("DIST_PACKAGES=%s", args.DistPackages),
		fmt.Sprintf("PIP_PACKAGES=%s", strings.Join(args.PipPackages, " ")),
	}
}

func (args *ImageBuildArgs) ToBuildArgsString() string {
	return strings.Join(args.ToBuildArgs(), "\n")
}

func NewBuildWorkflow(ctx context.Context, ir *ImageRepository) *GithubWorkflow {
	extras := ""
	project := ir.Project
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

	pipPackages := []string{"cryptography", "python-binary-memcached"}
	if val, ok := PIP_PACKAGES[project]; ok {
		pipPackages = append(pipPackages, val...)
	}

	platforms := "linux/amd64"
	if val, ok := PLATFORMS[project]; ok {
		platforms = val
	}

	gitRepo := fmt.Sprintf("https://github.com/openstack/%s", project)
	if _, ok := FORKED_PROJECTS[project]; ok {
		gitRepo = fmt.Sprintf("https://github.com/vexxhost/%s", project)
	}

	builderImageTag, err := getImageTag(ctx, ir.githubClient, "docker-openstack-builder", "openstack-builder-focal")
	if err != nil {
		builderImageTag = "latest"
	}

	runtimeImageTag, err := getImageTag(ctx, ir.githubClient, "docker-openstack-runtime", "openstack-runtime-focal")
	if err != nil {
		runtimeImageTag = "latest"
	}

	imageBuildArgs := ImageBuildArgs{
		BuilderImage:  fmt.Sprintf("quay.io/vexxhost/openstack-builder-${{ matrix.from }}:%s", builderImageTag),
		RuntimeImage: fmt.Sprintf("quay.io/vexxhost/openstack-runtime-${{ matrix.from }}:%s", runtimeImageTag),
		Release:      "${{ matrix.release }}",
		Project:      project,
		ProjectRepo:  gitRepo,
		ProjectRef:   "${{ env.PROJECT_REF }}",
		Extras:       extras,
		Profiles:     profiles,
		DistPackages: distPackages,
		PipPackages:  pipPackages,
	}
	imageVerifyCmds := []string{
		fmt.Sprintf("cosign verify --certificate-oidc-issuer=https://token.actions.githubusercontent.com --certificate-identity=https://github.com/vexxhost/docker-openstack-builder/.github/workflows/build.yml@refs/heads/main quay.io/vexxhost/openstack-builder-${{ matrix.from }}:%s", builderImageTag),
		fmt.Sprintf("cosign verify --certificate-oidc-issuer=https://token.actions.githubusercontent.com --certificate-identity=https://github.com/vexxhost/docker-openstack-runtime/.github/workflows/build.yml@refs/heads/main quay.io/vexxhost/openstack-runtime-${{ matrix.from }}:%s", runtimeImageTag),
	}

	releases := []string{"wallaby", "xena", "yoga", "zed", "2023.1", "2023.2"}
	if project == "keystone" {
		releases = []string{"zed", "2023.1", "2023.2"}
	}
	if project == "magnum" {
		releases = []string{"yoga", "zed", "2023.1", "2023.2"}
	}

	workflow := &GithubWorkflow{
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
				Permissions: map[string]string{
					"actions": "read",
					"contents": "read",
					"id-token": "write",
					"security-events": "write",
				},
				Strategy: GithubWorkflowStrategy{
					Matrix: map[string]interface{}{
						"from":    []string{"focal", "jammy"},
						"release": releases,
						"exclude": []map[string]string{
							{
								"from":    "focal",
								"release": "zed",
							},
							{
								"from":    "focal",
								"release": "2023.1",
							},
							{
								"from":    "focal",
								"release": "2023.2",
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
						Run:  "echo PROJECT_REF=$(cat manifest.yml | yq '.\"${{ matrix.release }}\".sha') >> $GITHUB_ENV",
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
						Name: "Install cosign",
						Uses: "sigstore/cosign-installer@main",
					},
					{
						Name: "Verify images",
						Run: strings.Join(imageVerifyCmds, "\n"),
					},
					{
						Name: "Build image",
						Uses: "docker/build-push-action@v3",
						Environment: map[string]string{
							"DOCKER_CONTENT_TRUST": "1",
						},
						With: map[string]string{
							"context":    ".",
							"cache-from": "type=gha,scope=${{ matrix.from }}-${{ matrix.release }}",
							"cache-to":   "type=gha,mode=max,scope=${{ matrix.from }}-${{ matrix.release }}",
							"load": "true",
							"build-args": imageBuildArgs.ToBuildArgsString(),
							"tags":       fmt.Sprintf("quay.io/vexxhost/%s:${{ env.PROJECT_REF }}-${{ matrix.from }}-${{ github.sha }}", project),
						},
					},
					{
						Name: "Scan image for vulnerabilities",
						Uses: "aquasecurity/trivy-action@master",
						With: map[string]string{
							"image-ref": fmt.Sprintf("quay.io/vexxhost/%s:${{ env.PROJECT_REF }}-${{ matrix.from }}-${{ github.sha }}", project),
							"format": "sarif",
							"output": "trivy-results.sarif",
							"ignore-unfixed": "true",
						},
					},
					{
						Name: "Upload scan result",
						Uses: "github/codeql-action/upload-sarif@v2",
						If:   "always()",
						With: map[string]string{
							"category": "${{ env.PROJECT_REF }}-${{ matrix.from }}",
							"sarif_file": "trivy-results.sarif",
						},
					},
					{
						Name: "Build image",
						Uses: "docker/build-push-action@v3",
						Id: "push-step",
						Environment: map[string]string{
							"DOCKER_CONTENT_TRUST": "1",
						},
						With: map[string]string{
							"context":    ".",
							"cache-from": "type=gha,scope=${{ matrix.from }}-${{ matrix.release }}",
							"cache-to":   "type=gha,mode=max,scope=${{ matrix.from }}-${{ matrix.release }}",
							"platforms":  platforms,
							"sbom": "true",
							"push":       "${{ github.event_name == 'push' }}",
							"build-args": imageBuildArgs.ToBuildArgsString(),
							"tags":       fmt.Sprintf("quay.io/vexxhost/%s:${{ env.PROJECT_REF }}-${{ matrix.from }}-${{ github.sha }}", project),
						},
					},
					{
						Name: "Promote image",
						Uses: "akhilerm/tag-push-action@v2.0.0",
						If:   `github.event_name == 'push' && ((matrix.from == 'focal') || (matrix.from == 'jammy' && matrix.release != 'yoga'))`,
						With: map[string]string{
							"src": fmt.Sprintf("quay.io/vexxhost/%s:${{ env.PROJECT_REF }}-${{ matrix.from }}-${{ github.sha }}", project),
							"dst": fmt.Sprintf("quay.io/vexxhost/%s:${{ matrix.release }}", project),
						},
					},
					{
						Name: "Sign the container image",
						If:   "${{ github.event_name == 'push' }}",
						Run: "cosign sign --yes quay.io/vexxhost/horizon@${{ steps.push-step.outputs.digest }}",
					},
				},
			},
		},
	}

	if project == "neutron" {
		infobloxImageBuildArgs := imageBuildArgs.DeepCopy()
		infobloxImageBuildArgs.PipPackages = append(infobloxImageBuildArgs.PipPackages, "networking-infoblox")

		workflow.Jobs["infoblox"] = workflow.Jobs["image"].DeepCopy()
		workflow.Jobs["infoblox"].Steps[5].With["cache-from"] += "-infoblox"
		workflow.Jobs["infoblox"].Steps[5].With["cache-to"] += "-infoblox"
		workflow.Jobs["infoblox"].Steps[5].With["tags"] = strings.ReplaceAll(workflow.Jobs["infoblox"].Steps[5].With["tags"], project, "neutron-infoblox")
		workflow.Jobs["infoblox"].Steps[5].With["build-args"] = infobloxImageBuildArgs.ToBuildArgsString()
		workflow.Jobs["infoblox"].Steps[6].With["src"] = strings.ReplaceAll(workflow.Jobs["infoblox"].Steps[6].With["src"], project, "neutron-infoblox")
		workflow.Jobs["infoblox"].Steps[6].With["dst"] = strings.ReplaceAll(workflow.Jobs["infoblox"].Steps[6].With["dst"], project, "neutron-infoblox")
	}

	return workflow
}
