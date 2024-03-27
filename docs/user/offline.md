# Install openstack-helm offline with Atmosphere

You can do a offline install openstack-helm using Atmosphere.

There are a couple of requirements to get this done:

- Docker image registry like [Harbor](https://goharbor.io/)
- Static webserver to service downloadable files
  - pip registry, you can also use the static webserver with [python-pypi-mirror](https://pypi.org/project/python-pypi-mirror/) installed.
  - On the webserver have a apt mirror, you can build the mirrors with [aptly](https://www.aptly.info/).

## Installing the nodes

Set the default ubuntu APT sources to the aptly repository's. This is not done by Atmosphere.

Set the pip repository in the file /etc/xdg/pip/pip.conf:

```ini
[global]
index-url = http://mirror.domain.tld/openstack-helm/python-kubernetes/kubernetes/
trusted-host = mirror.domain.tld
```

Use trusted-host when the index-url is a http webserver.

## Create PIP mirror

Use python-pypi-mirror to download the required pip packages.

The openstack-helm requires the following packages:

- kubernetes
- setuptools
- PyMySQL
- openstacksdk==0.61.0

The downloaded files will be saved in `download` directory. After that a pip repository will be created and the indexed will be placed in the directory `kubernetes`.

```shell
pip install python-pypi-mirror
pypi-mirror download -b -d download kubernetes setuptools PyMySQL openstacksdk==0.61.0
pypi-mirror create -d download -m kubernetes
```

## Set the configuration

The following images needs to be manual downloaded and the configuration variable needs to be set.

```yaml
octavia_amphora_image_url: "http://mirror.domain.tld/openstack-helm/images/test-only-amphora-x64-haproxy-ubuntu-focal.qcow2"

magnum_images:
  - name: ubuntu-2004-kube-v1.26.2
    url: http://mirror.domain.tld/openstack-helm/images/ubuntu-2004-v1.26.2.qcow2
    distro: ubuntu-focal
  - name: ubuntu-2204-kube-v1.26.6
    url: http://mirror.domain.tld/openstack-helm/images/ubuntu-2204-kube-v1.26.6.qcow2
    distro: ubuntu
  - name: ubuntu-2204-kube-v1.27.3
    url: http://mirror.domain.tld/openstack-helm/images/ubuntu-2204-kube-v1.27.3.qcow2
    distro: ubuntu

openstack_cli_cloud_archive_repo: deb http://mirror.domain.tld/ubuntu focal-updates-yoga main

ceph_repository_url: http://mirror.domain.tld/ceph/focal-ceph-pacific/
ceph_repository_apt_key: http://mirror.domain.tld/mirror.domain.tld.key

manila_image_url: "http://mirror.domain.tld/manila-{{ atmosphere_version }}.qcow2"

runc_download_url: http://mirror.domain.tld/openstack-helm/runc/{{ runc_version }}/runc.amd64
cni_plugins_download_url: http://mirror.domain.tld/openstack-helm/cni-plugins/{{ cni_plugins_version }}/cni-plugins-linux-amd64-{{ cni_plugins_version }}.tgz
kubelet_download_url: http://mirror.domain.tld/openstack-helm/kubernetes-release/v{{ kubelet_version }}/kubelet
containerd_download_url: http://mirror.domain.tld/openstack-helm/containerd/v{{ containerd_version }}/containerd-{{ containerd_version }}-linux-amd64.tar.gz
helm_download_url: http://mirror.domain.tld/openstack-helm/helm/{{ helm_version }}/helm-{{ helm_version }}-linux-amd64.tar.gz
helm_diff_download_url: http://mirror.domain.tld/openstack-helm/helm-diff/{{ helm_diff_version }}/helm-diff-linux-amd64.tgz
flux_download_url: http://mirror.domain.tld/openstack-helm/fluxcd/v{{ flux_version }}/flux_{{ flux_version }}_linux_amd64.tar.gz
kubeadm_download_url: http://mirror.domain.tld/openstack-helm/kubernetes-release/v{{ kubeadm_version }}/kubeadm
clusterctl_download_url: http://mirror.domain.tld/openstack-helm/cluster-api/v{{ clusterctl_version }}/clusterctl-linux-amd64
cri_tools_crictl_download_url: http://mirror.domain.tld/openstack-helm/cri-tools/{{ cri_tools_version }}/crictl-{{ cri_tools_version }}-linux-amd64.tar.gz
cri_tools_critest_download_url: http://mirror.domain.tld/openstack-helm/cri-tools/{{ cri_tools_version }}/critest-{{ cri_tools_version }}-linux-amd64.tar.gz
kubectl_download_url: http://mirror.domain.tld/openstack-helm/kubernetes-release/v{{ kubectl_version }}/kubectl
```

## Mirror the docker images

You can mirror the images and so upload the copy to the registry with [image_manifest](https://github.com/vexxhost/atmosphere/tree/main/roles/image_manifest).

```shell
poetry run ansible-playbook -v vexxhost.atmosphere.image_manifest -e image_manifest_registry=registry.domain.tld/openstack-helm/infra -e image_manifest_path=/tmp/atmosphere_images.yml -e image_manifest_mirror=true
```

This playbook generates the file /tmp/atmosphere_images.yml with the variable atmosphere_images.

In this hash you have all the image names that is required for k8s and openstack-helm.
