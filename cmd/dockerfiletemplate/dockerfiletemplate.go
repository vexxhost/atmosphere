package main

import (
	"bytes"
	"fmt"
	"text/template"

	"github.com/Masterminds/sprig/v3"
	"github.com/go-git/go-git/v6"
	"github.com/go-git/go-git/v6/plumbing"
	"github.com/go-git/go-git/v6/storage/memory"
	"github.com/mdomke/git-semver/v6/version"
)

func main() {
	images := map[string]*dockerImageSpec{
		"barbican": {
			Wheels: []dockerImageWheel{
				{
					Name:          "openstack/barbican",
					GitRepository: "https://opendev.org/openstack/barbican.git",
					GitBranch:     "master",
					GitReference:  "9f1f1c66a841ab8150e8c1c1bdb529f190086c2f",
				},
			},
			PythonPackages: []string{"pykmip"},
		},
		"cinder": {
			Wheels: []dockerImageWheel{
				{
					Name:          "openstack/cinder",
					GitRepository: "https://opendev.org/openstack/cinder.git",
					GitBranch:     "master",
					GitReference:  "256e26e54d71caf16f1aecc4df6b670d814ba18b",
				},
			},
			PythonPackages: []string{"purestorage", "python-3parclient", "storpool", "storpool.spopenstack"},
			SystemPackages: []string{"ceph-common", "dmidecode", "lsscsi", "nfs-common", "nvme-cli", "python3-rados", "python3-rbd", "qemu-utils", "qemu-block-extra", "sysfsutils", "udev", "util-linux"},
		},
		"manila": {
			Wheels: []dockerImageWheel{
				{
					Name:          "openstack/manila",
					GitRepository: "https://opendev.org/openstack/manila.git",
					GitBranch:     "master",
					GitReference:  "a0bc45101880ddd80f9240ab75e9f3fead9f4ba4",
				},
			},
			SystemPackages: []string{"iproute2", "openvswitch-switch"},
		},
	}

	dockerfile, err := images["manila"].Dockerfile()
	if err != nil {
		panic(err)
	}

	println(dockerfile)
}

type dockerImageSpec struct {
	Wheels         []dockerImageWheel
	PythonPackages []string
	SystemPackages []string
}

func (d *dockerImageSpec) Dockerfile() (string, error) {
	tmpl, err := template.New("dockerfile.tmpl").Funcs(sprig.FuncMap()).ParseFiles("cmd/dockerfiletemplate/dockerfile.tmpl")
	if err != nil {
		return "", err
	}

	var buf bytes.Buffer
	err = tmpl.Execute(&buf, d)
	if err != nil {
		return "", err
	}

	return buf.String(), nil
}

type dockerImageWheel struct {
	Name          string
	GitRepository string
	GitBranch     string
	GitReference  string
}

func (dc *dockerImageWheel) Version() (*version.Version, error) {
	repo, err := git.Clone(memory.NewStorage(), nil, &git.CloneOptions{
		URL:           dc.GitRepository,
		ReferenceName: plumbing.NewBranchReferenceName(dc.GitBranch),
		SingleBranch:  true,
	})
	if err != nil {
		return nil, err
	}

	err = repo.Storer.SetReference(plumbing.NewHashReference(
		plumbing.HEAD,
		plumbing.NewHash(dc.GitReference),
	))
	if err != nil {
		return nil, err
	}

	head, err := version.GitDescribeRepository(repo)
	if err != nil {
		return nil, err
	}

	fmt.Println(head)

	version, err := version.NewFromHead(head, "")
	if err != nil {
		return nil, err
	}

	return &version, nil
}

func (dc *dockerImageWheel) PbrVersion() (string, error) {
	gitVersion, err := dc.Version()
	if err != nil {
		return "", err
	}

	return gitVersion.Format(version.NoMetaFormat)
}
