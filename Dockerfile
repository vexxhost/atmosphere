# syntax=docker/dockerfile-upstream:master-labs

ARG BASE_IMAGE=docker.io/alpine:3.17

# Build the internal Helm repository server
FROM ${BASE_IMAGE} AS helm-repository
RUN --mount=type=cache,target=/var/cache/apk <<EOF /bin/sh -e
  apk add \
    bash \
    helm
EOF
ADD images/atmosphere/helm-repository/repository-list /var/lib/atmosphere/repository-list
ADD images/atmosphere/helm-repository/chart-list /var/lib/atmosphere/chart-list
ADD images/atmosphere/helm-repository/mirror-charts /usr/local/bin/mirror-charts
RUN chmod +x /usr/local/bin/mirror-charts
RUN /usr/local/bin/mirror-charts /var/lib/atmosphere/repository-list /var/lib/atmosphere/chart-list

FROM python:3.10-slim AS poetry
RUN --mount=type=cache,target=/root/.cache <<EOF
  pip install poetry
EOF

FROM poetry AS builder
RUN <<EOF
  apt-get update
  apt-get install -y build-essential
EOF
WORKDIR /app
ADD poetry.lock /app
ADD pyproject.toml /app
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN poetry install --only main --extras operator --no-root --no-interaction
ADD . /app
RUN poetry install --only main --extras operator --no-interaction

FROM python:3.10-slim AS kubectl
ADD https://dl.k8s.io/release/v1.26.0/bin/linux/amd64/kubectl /kubectl
RUN chmod +x /kubectl
RUN /kubectl version --client

FROM python:3.10-slim AS helm
ADD https://get.helm.sh/helm-v3.10.2-linux-amd64.tar.gz /helm.tar.gz
RUN tar -xvzf /helm.tar.gz
RUN /linux-amd64/helm version

FROM python:3.10-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder --link /app /app
COPY --from=kubectl --link /kubectl /usr/local/bin/kubectl
COPY --from=helm --link /linux-amd64/helm /usr/local/bin/helm
COPY --from=helm-repository --link /charts /charts
ADD images/atmosphere/helm-repository/nginx.conf /etc/nginx/nginx.conf
