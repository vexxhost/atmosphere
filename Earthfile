VERSION --use-copy-link 0.7
FROM python:3.10

poetry:
  RUN pip3 install poetry==1.4.2
  SAVE IMAGE --cache-hint

build.wheels:
  FROM +poetry
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
  FROM python:3.10-slim
  COPY +build.venv.runtime/venv /venv
  COPY +build.collections/ /usr/share/ansible
  ENV ANSIBLE_PIPELINING=True
  ENV PATH=/venv/bin:$PATH
  RUN \
    apt-get update && \
    apt-get install --no-install-recommends -y rsync openssh-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
  ENTRYPOINT ["/bin/bash", "-l", "-c"]
  ARG tag=latest
  SAVE IMAGE --push ghcr.io/vexxhost/atmosphere:${tag}

pin-images:
  FROM +build.venv.dev
  COPY roles/defaults/defaults/main.yml /defaults.yml
  COPY build/pin-images.py /usr/local/bin/pin-images
  RUN /usr/local/bin/pin-images /defaults.yml /pinned.yml
  SAVE ARTIFACT /pinned.yml AS LOCAL roles/defaults/defaults/main.yml

gh:
  FROM alpine:3
  RUN apk add --no-cache github-cli

trigger-image-sync:
  FROM +gh
  ARG --required project
  RUN --secret GITHUB_TOKEN gh workflow run --repo vexxhost/docker-openstack-${project} sync.yml
