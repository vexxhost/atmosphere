################################################
Install openstack-helm airgapped with Atmosphere
################################################

You can do a offline install with Atmosphere.

There are a couple of requirements to get this done:

- Docker image registry like [Harbor](https://goharbor.io/)
- Static webserver to service downloadable files
  - pip registry, you can also use the static webserver with [python-pypi-mirror](https://pypi.org/project/python-pypi-mirror/) installed.
  - On the webserver have a apt mirror, you can build the mirrors with [aptly](https://www.aptly.info/).

With this Airgapped install you only need to have internet / proxy when you use external authentication or monitoring.

********************
Installing the nodes
********************

Set the default ubuntu APT sources to the aptly repository's. This is not done by Atmosphere.

Set the pip repository in the file /etc/xdg/pip/pip.conf:

.. code-block:: yaml

  [global]
  index-url = http://mirror.domain.tld/imageMirror/piprepo/
  trusted-host = mirror.domain.tld

Use trusted-host when the index-url is a http webserver.

*****************
Create PIP mirror
*****************

Use python-pypi-mirror to download the required pip packages.

The openstack-helm requires the following packages:

- kubernetes
- setuptools
- PyMySQL
- openstacksdk==0.61.0

The downloaded files will be saved in `downloads` directory. After that a pip repository will be created and the indexed will be placed in the directory `kubernetes`.

.. code-block:: bash

  pip install python-pypi-mirror
  pypi-mirror download -b -d /downloads kubernetes==29.0.0 osc-placement==4.3.0 "pyopenssl>=22.1.0" PyMySQL
  pypi-mirror download --python-version 3.8 --platform manylinux2014_x86_64 -b -d /downloads "pyyaml==5.4.1"
  pypi-mirror download -b -d /downloads "pyyaml==5.3.1"
  pypi-mirror download --python-version 3.8 --platform manylinux2014_x86_64 -b -d /downloads "cryptography<43,>=41.0.5"
  pypi-mirror download --python-version 3.8 --platform manylinux_2_17_x86_64 -b -d /downloads "cryptography<43,>=41.0.5"
  pypi-mirror download -b -d /downloads openstacksdk==0.61.0
  pypi-mirror create -c -d downloads -m /usr/share/nginx/html/imageMirror/piprepo


*********************
Set the configuration
*********************

The following images needs to be manual downloaded and the configuration variable needs to be set.

.. code-block:: yaml

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

*********************************
Using Earthly to build the images
*********************************

You can use the following Earth file to create a image containing all the static and PIP files.


.. code-block:: Dockerfile
  :linenos:

  VERSION --use-copy-link 0.8

  # version 0.6

  pip:
    FROM python:3.10
    RUN pip install python-pypi-mirror
    RUN mkdir -p /piprepo
    RUN mkdir /downloads
    RUN pypi-mirror download -b -d /downloads kubernetes==29.0.0 osc-placement==4.3.0 "pyopenssl>=22.1.0" PyMySQL
    RUN pypi-mirror download --python-version 3.8 --platform manylinux2014_x86_64 -b -d /downloads "pyyaml==5.4.1"
    RUN pypi-mirror download -b -d /downloads "pyyaml==5.3.1"
    RUN pypi-mirror download --python-version 3.8 --platform manylinux2014_x86_64 -b -d /downloads "cryptography<43,>=41.0.5"
    RUN pypi-mirror download --python-version 3.8 --platform manylinux_2_17_x86_64 -b -d /downloads "cryptography<43,>=41.0.5"
    RUN pypi-mirror download -b -d /downloads openstacksdk==0.61.0
    RUN pypi-mirror create -c -d downloads -m /piprepo
    SAVE ARTIFACT /piprepo
    SAVE IMAGE --cache-hint pip

  curl:
    FROM ubuntu:22.04
    RUN \
      apt-get update && \
      apt-get install --no-install-recommends -y nano curl wget curl ca-certificates && \
      apt-get clean && \
      rm -rf /var/lib/apt/lists/*
    RUN mkdir /files

    # download kail
    RUN curl -L -s -S https://github.com/boz/kail/releases/download/v0.17.4/kail_v0.17.4_linux_amd64.tar.gz -o /tmp/kail_v0.17.4_linux_amd64.tar.gz && \
        mkdir -p /files/kubectl-plugins/ && \
        tar -xvzf /tmp/kail_v0.17.4_linux_amd64.tar.gz -C /files/kubectl-plugins/ kail && \
        mv /files/kubectl-plugins/kail /files/kubectl-plugins/kailv0.17.4

    # download runc
    RUN mkdir -p /files/runc/v1.1.4/ && \
        curl -L -s -S https://github.com/opencontainers/runc/releases/download/v1.1.4/runc.amd64 -o /files/runc/v1.1.4/runc.amd64

    # download runc.amd64
    RUN mkdir -p /files/runc/v1.1.10/ && \
        curl -L -s -S https://github.com/opencontainers/runc/releases/download/v1.1.10/runc.amd64 -o /files/runc/v1.1.10/runc.amd64

    # download cni-plugins
    RUN mkdir -p /files/cni-plugins/v1.3.0 && \
        curl -L -s -S https://github.com/containernetworking/plugins/releases/download/v1.3.0/cni-plugins-linux-amd64-v1.3.0.tgz -o /files/cni-plugins/v1.3.0/cni-plugins-linux-amd64-v1.3.0.tgz

    # download kubelet
    RUN mkdir -p /files/kubernetes-release/v1.22.17/ && \
        curl -L -s -S https://storage.googleapis.com/kubernetes-release/release/v1.22.17/bin/linux/amd64/kubelet -o /files/kubernetes-release/v1.22.17/kubelet

    # download containerd
    RUN mkdir -p /files/containerd/v1.7.0/ && \
        curl -L -s -S https://github.com/containerd/containerd/releases/download/v1.7.0/containerd-1.7.0-linux-amd64.tar.gz -o /files/containerd/v1.7.0/containerd-1.7.0-linux-amd64.tar.gz

    # download containerd
    RUN mkdir -p /files/containerd/v1.7.9/ && \
        curl -L -s -S https://github.com/containerd/containerd/releases/download/v1.7.9/containerd-1.7.9-linux-amd64.tar.gz -o /files/containerd/v1.7.9/containerd-1.7.9-linux-amd64.tar.gz

    # download helm
    RUN mkdir -p /files/helm/v3.11.2/ && \
        curl -L -s -S https://get.helm.sh/helm-v3.11.2-linux-amd64.tar.gz -o /files/helm/v3.11.2/helm-v3.11.2-linux-amd64.tar.gz

    # download helm-diff
    RUN mkdir -p /files/helm-diff/v3.8.1/ && \
        curl -L -s -S https://github.com/databus23/helm-diff/releases/download/v3.8.1/helm-diff-linux-amd64.tgz -o /files/helm-diff/v3.8.1/helm-diff-linux-amd64.tgz

    # download flux
    RUN mkdir -p /files/fluxcd/v0.32.0/ && \
        curl -L -s -S https://github.com/fluxcd/flux2/releases/download/v0.32.0/flux_0.32.0_linux_amd64.tar.gz -o /files/fluxcd/v0.32.0/flux_0.32.0_linux_amd64.tar.gz

    # download kubeadm
    RUN mkdir -p /files/kubernetes-release/v1.22.17/ && \
        curl -L -s -S https://storage.googleapis.com/kubernetes-release/release/v1.22.17/bin/linux/amd64/kubeadm -o /files/kubernetes-release/v1.22.17/kubeadm

    # download clusterctl
    RUN mkdir -p /files/cluster-api/v1.5.1/ && \
        curl -L -s -S https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.5.1/clusterctl-linux-amd64 -o /files/cluster-api/v1.5.1/clusterctl-linux-amd64

    # download clusterctl
    RUN mkdir -p /files/cluster-api/v1.6.0/ && \
        curl -L -s -S https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.6.0/clusterctl-linux-amd64 -o /files/cluster-api/v1.6.0/clusterctl-linux-amd64

    # download crictl
    RUN mkdir -p /files/cri-tools/v1.25.0/ && \
        curl -L -s -S https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.25.0/crictl-v1.25.0-linux-amd64.tar.gz -o /files/cri-tools/v1.25.0/crictl-v1.25.0-linux-amd64.tar.gz

    # download crictl
    RUN mkdir -p /files/cri-tools/v1.28.0/ && \
        curl -L -s -S https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.28.0/crictl-v1.28.0-linux-amd64.tar.gz -o /files/cri-tools/v1.28.0/crictl-v1.28.0-linux-amd64.tar.gz

    # download critest
    RUN mkdir -p /files/cri-tools/v1.25.0/ && \
        curl -L -s -S https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.25.0/critest-v1.25.0-linux-amd64.tar.gz -o /files/cri-tools/v1.25.0/critest-v1.25.0-linux-amd64.tar.gz

    # download critest
    RUN mkdir -p /files/cri-tools/v1.28.0/ && \
        curl -L -s -S https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.28.0/critest-v1.28.0-linux-amd64.tar.gz -o /files/cri-tools/v1.28.0/critest-v1.28.0-linux-amd64.tar.gz

    # download kubectl
    RUN mkdir -p /files/kubernetes-release/v1.22.17/ && \
        curl -L -s -S https://storage.googleapis.com/kubernetes-release/release/v1.22.17/bin/linux/amd64/kubectl -o /files/kubernetes-release/v1.22.17/kubectl

    # download cephadm
    RUN mkdir -p /files/ceph/quincy/ && \
        curl -L -s -S http://apt.cgm.ag/openstack-helm/ceph/quincy/cephadm -o /files/ceph/quincy/cephadm

    SAVE ARTIFACT /files
    SAVE IMAGE --cache-hint

  image:
    FROM nginx:stable
    RUN mkdir -p /usr/share/nginx/html/imageMirror
    COPY +curl/files /usr/share/nginx/html/imageMirror
    COPY +pip/piprepo /usr/share/nginx/html/imageMirror/piprepo
    ARG IMAGE_TAG=${IMAGE_TAG}
    ARG REGISTRY_SERVER=regi.c3.cgm.ag
    ARG REGISTRY=${REGISTRY_SERVER}/atmosphere
    SAVE IMAGE --push ${REGISTRY}/imagemirror:${IMAGE_TAG}

************************
Mirror the docker images
************************

You can mirror the images and so upload the copy to the registry with `image_manifest <https://github.com/vexxhost/atmosphere/tree/main/roles/image_manifest>`_.

.. code-block:: shell

  poetry run ansible-playbook \
    -v vexxhost.atmosphere.image_manifest \
    -e image_manifest_registry=registry.domain.tld/openstack-helm/infra \
    -e image_manifest_path=/tmp/atmosphere_images.yml \
    -e image_manifest_mirror=true

This playbook generates the file /tmp/atmosphere_images.yml with the variable atmosphere_images.

In this hash you have all the image names that is required for k8s and openstack-helm.
