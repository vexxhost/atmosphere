VERSION --use-copy-link --try 0.8

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

build.venv.runtime:
  FROM ubuntu:jammy
  RUN \
    apt-get update -qq
  RUN \
    apt-get install -qq -y --no-install-recommends \
      build-essential git python3-dev python3-pip python3-venv
  COPY requirements.txt ./
  RUN python3 -m venv /venv
  ENV PATH=/venv/bin:$PATH
  RUN pip install -r requirements.txt
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
      python3 rsync openssh-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
  COPY +build.venv.runtime/venv /venv
  ENV PATH=/venv/bin:$PATH
  COPY +build.collections/ /usr/share/ansible
  ARG tag=latest
  ARG REGISTRY=ghcr.io/vexxhost/atmosphere
  SAVE IMAGE --push ${REGISTRY}:${tag}
