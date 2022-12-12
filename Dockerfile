# syntax=docker/dockerfile-upstream:master-labs

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
RUN poetry install --only main --no-root --no-interaction
ADD . /app
RUN poetry install --only main --no-interaction

FROM python:3.10-slim AS helm
ADD https://get.helm.sh/helm-v3.10.2-linux-amd64.tar.gz /helm.tar.gz
ADD https://dl.k8s.io/release/v1.26.0/bin/linux/amd64/kubectl /kubectl
RUN tar -xvzf /helm.tar.gz
RUN /linux-amd64/helm version

FROM python:3.10-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder --link /app /app
COPY --from=helm --link /linux-amd64/helm /usr/local/bin/helm
COPY --from=helm --link /kubectl /usr/local/bin/kubectl
CMD ["kopf", "run", "/app/atmosphere/cmd/operator.py"]
