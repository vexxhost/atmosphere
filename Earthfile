VERSION --use-copy-link --try 0.8

lint:
  BUILD +lint.ansible-lint
  BUILD +lint.markdownlint

lint.markdownlint:
  FROM davidanson/markdownlint-cli2
  COPY --dir docs/ .markdownlint.yaml .markdownlint-cli2.jsonc /src
  WORKDIR /src
  TRY
    RUN markdownlint-cli2 **
  FINALLY
    SAVE ARTIFACT /src/junit.xml AS LOCAL junit.xml
  END

lint.ansible-lint:
  FROM registry.gitlab.com/pipeline-components/ansible-lint:latest
  COPY --dir meta/ molecule/ playbooks/ plugins/ roles/ tests/ .ansible-lint CHANGELOG.md galaxy.yml /code
  TRY
    RUN ansible-lint -v --show-relpath -f pep8 --nocolor | ansible-lint-junit -o ansible-lint.xml
  FINALLY
    SAVE ARTIFACT ansible-lint.xml AS LOCAL ansible-lint.xml
  END

unit.go:
  FROM golang:1.21
  RUN go install github.com/jstemmer/go-junit-report/v2@latest
  COPY --dir go.mod go.sum /src
  WORKDIR /src
  RUN go mod download
  COPY --dir charts/ cmd/ internal/ roles/ tools/ /src
  TRY
    RUN go test -v 2>&1 ./... | go-junit-report -set-exit-code > junit-go.xml
  FINALLY
    SAVE ARTIFACT /src/junit-go.xml AS LOCAL junit-go.xml
  END

build.collection:
  FROM registry.gitlab.com/pipeline-components/ansible-lint:latest
  COPY . /src
  RUN ansible-galaxy collection build /src
  SAVE ARTIFACT /code/*.tar.gz AS LOCAL dist/

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
  ARG REGISTRY=ghcr.io/vexxhost/atmosphere
  SAVE IMAGE --push ${REGISTRY}/libvirt-tls-sidecar:latest

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
  ARG REGISTRY=ghcr.io/vexxhost/atmosphere
  SAVE IMAGE --push ${REGISTRY}:${tag}

images:
  ARG REGISTRY=ghcr.io/vexxhost/atmosphere
  BUILD +libvirt-tls-sidecar.image --REGISTRY=${REGISTRY}
  BUILD ./images/cinder+image --REGISTRY=${REGISTRY}
  BUILD ./images/cluster-api-provider-openstack+image --REGISTRY=${REGISTRY}
  BUILD ./images/designate+image --REGISTRY=${REGISTRY}
  BUILD ./images/glance+image --REGISTRY=${REGISTRY}
  BUILD ./images/heat+image --REGISTRY=${REGISTRY}
  BUILD ./images/horizon+image --REGISTRY=${REGISTRY}
  BUILD ./images/ironic+image --REGISTRY=${REGISTRY}
  BUILD ./images/keystone+image --REGISTRY=${REGISTRY}
  BUILD ./images/kubernetes-entrypoint+image --REGISTRY=${REGISTRY}
  BUILD ./images/libvirtd+image --REGISTRY=${REGISTRY}
  BUILD ./images/magnum+image --REGISTRY=${REGISTRY}
  BUILD ./images/manila+image --REGISTRY=${REGISTRY}
  BUILD ./images/netoffload+image --REGISTRY=${REGISTRY}
  BUILD ./images/neutron+image --REGISTRY=${REGISTRY}
  BUILD ./images/nova-ssh+image --REGISTRY=${REGISTRY}
  BUILD ./images/nova+image --REGISTRY=${REGISTRY}
  BUILD ./images/octavia+image --REGISTRY=${REGISTRY}
  BUILD ./images/openvswitch+image --REGISTRY=${REGISTRY}
  BUILD ./images/ovn+images --REGISTRY=${REGISTRY}
  BUILD ./images/placement+image --REGISTRY=${REGISTRY}
  BUILD ./images/senlin+image --REGISTRY=${REGISTRY}
  BUILD ./images/staffeln+image --REGISTRY=${REGISTRY}
  BUILD ./images/tempest+image --REGISTRY=${REGISTRY}

SCAN_IMAGE:
  FUNCTION
  ARG --required IMAGE
  # TODO(mnaser): Include secret scanning when it's more reliable.
  RUN \
    trivy image \
      --skip-db-update \
      --skip-java-db-update \
      --scanners vuln \
      --exit-code 1 \
      --ignore-unfixed \
      --timeout 10m \
      ${IMAGE}

scan-image:
  FROM ./images/trivy+image
  ARG --required IMAGE
  DO +SCAN_IMAGE --IMAGE ${IMAGE}

scan-images:
  FROM ./images/trivy+image
  COPY roles/defaults/vars/main.yml /defaults.yml
  # TODO(mnaser): Scan all images eventually
  FOR IMAGE IN $(cat /defaults.yml | egrep -E 'ghcr.io/vexxhost|registry.atmosphere.dev' | cut -d' ' -f4 | sort | uniq)
    BUILD +scan-image --IMAGE ${IMAGE}
  END

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
