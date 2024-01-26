VERSION --use-copy-link 0.7

go.build:
  FROM golang:1.21
  WORKDIR /src
  ARG GOOS=linux
  ARG GOARCH=amd64
  ARG VARIANT
  COPY --dir go.mod go.sum ./
  RUN go mod download

libvirt-tls-sidecar.build:
  FROM +go.build
  ARG GOOS=linux
  ARG GOARCH=amd64
  ARG VARIANT
  COPY --dir cmd internal ./
  RUN GOARM=${VARIANT#"v"} go build -o main cmd/libvirt-tls-sidecar/main.go
  SAVE ARTIFACT ./main

libvirt-tls-sidecar.platform-image:
  ARG TARGETPLATFORM
  ARG TARGETARCH
  ARG TARGETVARIANT
  FROM --platform=$TARGETPLATFORM ./images/base+image
  COPY \
    --platform=linux/amd64 \
    (+libvirt-tls-sidecar.build/main --GOARCH=$TARGETARCH --VARIANT=$TARGETVARIANT) /usr/bin/libvirt-tls-sidecar
  ENTRYPOINT ["/usr/bin/libvirt-tls-sidecar"]
  SAVE IMAGE --push ghcr.io/vexxhost/atmosphere/libvirt-tls-sidecar:latest

libvirt-tls-sidecar.image:
    BUILD --platform=linux/amd64 --platform=linux/arm64 +libvirt-tls-sidecar.platform-image

build.wheels:
  FROM ./images/builder+image
  COPY pyproject.toml poetry.lock ./
  ARG --required only
  RUN poetry export --only=${only} -f requirements.txt --without-hashes > requirements.txt
  RUN pip wheel -r requirements.txt --wheel-dir=/wheels
  SAVE ARTIFACT requirements.txt
  SAVE ARTIFACT /wheels
  SAVE IMAGE --cache-hint

build.venv:
  ARG --required only
  FROM +build.wheels --only ${only}
  RUN python3 -m venv /venv
  ENV PATH=/venv/bin:$PATH
  RUN pip install -r requirements.txt
  SAVE IMAGE --cache-hint

build.venv.dev:
  FROM +build.venv --only main,dev
  SAVE ARTIFACT /venv

build.venv.runtime:
  FROM +build.venv --only main
  SAVE ARTIFACT /venv

build.collections:
  FROM +build.venv.runtime
  COPY charts /src/charts
  COPY meta /src/meta
  COPY playbooks /src/playbooks
  COPY plugins /src/plugins
  COPY roles /src/roles
  COPY galaxy.yml /src/galaxy.yml
  RUN ansible-galaxy collection install --collections-path /usr/share/ansible/collections /src
  SAVE ARTIFACT /usr/share/ansible/collections
  SAVE IMAGE --cache-hint

image:
  ARG RELEASE=2023.1
  FROM ./images/cloud-archive-base+image --RELEASE ${RELEASE}
  ENV ANSIBLE_PIPELINING=True
  DO ./images+APT_INSTALL --PACKAGES "rsync openssh-client"
  COPY +build.venv.runtime/venv /venv
  ENV PATH=/venv/bin:$PATH
  COPY +build.collections/ /usr/share/ansible
  ARG tag=latest
  SAVE IMAGE --push ghcr.io/vexxhost/atmosphere:${tag}

images:
  BUILD +libvirt-tls-sidecar.image
  BUILD ./images/barbican+image
  BUILD ./images/cinder+image
  BUILD ./images/cluster-api-provider-openstack+image
  BUILD ./images/designate+image
  BUILD ./images/glance+image
  BUILD ./images/heat+image
  BUILD ./images/horizon+image
  BUILD ./images/ironic+image
  BUILD ./images/keystone+image
  BUILD ./images/kubernetes-entrypoint+image
  BUILD ./images/libvirtd+image
  BUILD ./images/magnum+image
  BUILD ./images/manila+image
  BUILD ./images/netoffload+image
  BUILD ./images/neutron+image
  BUILD ./images/nova-ssh+image
  BUILD ./images/nova+image
  BUILD ./images/octavia+image
  BUILD ./images/openvswitch+image
  BUILD ./images/ovn+images
  BUILD ./images/placement+image
  BUILD ./images/senlin+image
  BUILD ./images/staffln+image
  BUILD ./images/tempest+image

SCAN_IMAGE:
  COMMAND
  ARG --required IMAGE
  # TODO(mnaser): Include secret scanning when it's more reliable.
  RUN \
    trivy image \
      --skip-db-update \
      --skip-java-db-update \
      --scanners vuln \
      --exit-code 1 \
      --ignore-unfixed \
      ${IMAGE}

scan-image:
  FROM ./images/trivy+image
  ARG --required IMAGE
  DO +SCAN_IMAGE --IMAGE ${IMAGE}

scan-images:
  FROM ./images/trivy+image
  COPY roles/defaults/vars/main.yml /defaults.yml
  # TODO(mnaser): Scan all images eventually
  FOR IMAGE IN $(cat /defaults.yml | grep 'ghcr.io/vexxhost' | cut -d' ' -f4 | sort | uniq)
    BUILD +scan-image --IMAGE ${IMAGE}
    # DO +SCAN_IMAGE --IMAGE ${IMAGE}
  END

pin-images:
  FROM +build.venv.dev
  COPY roles/defaults/vars/main.yml /defaults.yml
  COPY build/pin-images.py /usr/local/bin/pin-images
  RUN --no-cache /usr/local/bin/pin-images /defaults.yml /pinned.yml
  SAVE ARTIFACT /pinned.yml AS LOCAL roles/defaults/vars/main.yml

gh:
  FROM alpine:3
  RUN apk add --no-cache github-cli

trigger-image-sync:
  FROM +gh
  ARG --required project
  RUN --secret GITHUB_TOKEN gh workflow run --repo vexxhost/docker-openstack-${project} sync.yml

image-sync:
  FROM golang:1.19
  ARG --required project
  WORKDIR /src
  COPY . /src
  RUN --secret GITHUB_TOKEN go run ./cmd/atmosphere-ci image repo sync ${project}

mkdocs-image:
  FROM ghcr.io/squidfunk/mkdocs-material:9.5.4
  RUN pip install \
    mkdocs-literate-nav
  SAVE IMAGE mkdocs

mkdocs-serve:
  LOCALLY
  WITH DOCKER --load=+mkdocs-image
    RUN docker run --rm -p 8000:8000 -v ${PWD}:/docs mkdocs
  END

mkdocs-build:
  FROM +mkdocs-image
  COPY . /docs
  RUN mkdocs build
  RUN --push --secret GITHUB_TOKEN git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/vexxhost/atmosphere.git
  RUN --push mkdocs gh-deploy --force
