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

builder:
  FROM ubuntu:jammy
  RUN apt-get update -qq
  RUN \
    apt-get install -qq -y --no-install-recommends \
      build-essential git python3-dev python3-pip python3-venv
  ARG POETRY_VERSION=1.4.2
  RUN pip3 install --no-cache-dir poetry==${POETRY_VERSION}

build.collection:
  FROM registry.gitlab.com/pipeline-components/ansible-lint:latest
  COPY . /src
  RUN ansible-galaxy collection build /src
  SAVE ARTIFACT /code/*.tar.gz AS LOCAL dist/

build.wheels:
  FROM +builder
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
  FROM ubuntu:jammy
  ENV ANSIBLE_PIPELINING=True
  RUN \
    apt-get update -qq && \
    apt-get install -qq -y --no-install-recommends \
      rsync openssh-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
  COPY +build.venv.runtime/venv /venv
  ENV PATH=/venv/bin:$PATH
  COPY +build.collections/ /usr/share/ansible
  ARG tag=latest
  ARG REGISTRY=ghcr.io/vexxhost/atmosphere
  SAVE IMAGE --push ${REGISTRY}:${tag}

pin-images:
  FROM +build.venv.dev
  COPY roles/defaults/vars/main.yml /defaults.yml
  COPY build/pin-images.py /usr/local/bin/pin-images
  ARG REGISTRY=ghcr.io/vexxhost/atmosphere
  RUN --no-cache /usr/local/bin/pin-images --registry ${REGISTRY} /defaults.yml /pinned.yml
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
