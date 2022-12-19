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
RUN /usr/local/bin/mirror-charts /var/lib/atmosphere/repository-list /var/lib/atmosphere/chart-list

# Create image for Python builder
FROM ${BASE_IMAGE} AS python-builder
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN --mount=type=cache,target=/var/cache/apk <<EOF /bin/sh -e
  apk add \
    poetry
EOF
WORKDIR /app
ADD poetry.lock /app/poetry.lock
ADD pyproject.toml /app/pyproject.toml
RUN poetry install --only main --no-root --no-interaction

# Build operator virtual environment
FROM python-builder AS operator-builder
RUN --mount=type=cache,target=/var/cache/apk <<EOF /bin/sh -e
  apk add \
    g++ \
    gcc \
    linux-headers \
    make \
    musl-dev \
    python3-dev
EOF
RUN poetry install --only operator --no-root --no-interaction
ADD . /app
RUN poetry install --only operator --no-interaction

# Build CLI virtual environment
FROM python-builder AS cli-builder
RUN poetry install --only cli --no-root --no-interaction
ADD atmosphere/cmd/cli.py /app/atmosphere/cmd/cli.py
ADD atmosphere/operator/constants.py /app/atmosphere/operator/constants.py
ADD atmosphere/operator/utils.py /app/atmosphere/operator/utils.py
ADD README.md /app/README.md
RUN poetry install --only cli --no-interaction

# Start up temporary registry to pre-load data
FROM ${BASE_IMAGE} AS build-registry
RUN --mount=type=cache,target=/var/cache/apk <<EOF /bin/sh -e
  apk add \
    bash \
    docker-registry \
    python3 \
    skopeo
EOF
ADD images/atmosphere/registry/config.yml /etc/docker-registry/config.yml
COPY --from=cli-builder --link /app /app
RUN <<EOF /bin/bash -e
docker-registry serve /etc/docker-registry/config.yml &>/dev/null &
/app/.venv/bin/atmosphere image mirror localhost:5000
# TODO: Bundle Magnum images
pkill docker-registry
EOF

# Build run-time image
FROM ${BASE_IMAGE} AS operator
ENV PATH="/app/.venv/bin:$PATH"
RUN --mount=type=cache,target=/var/cache/apk <<EOF /bin/sh -e
  apk add \
    docker-registry \
    helm \
    libstdc++ \
    nginx \
    python3
EOF
COPY --from=docker.io/alpine/k8s:1.26.0 /usr/bin/kubectl /usr/bin/kubectl
COPY --from=build-registry --link /var/lib/registry /var/lib/registry
COPY --from=helm-repository --link /charts /charts
COPY --from=operator-builder --link /app /app
ADD images/atmosphere/helm-repository/nginx.conf /etc/nginx/nginx.conf
ADD images/atmosphere/registry/config.yml /etc/docker-registry/config.yml
