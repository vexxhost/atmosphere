# syntax=docker/dockerfile-upstream:master-labs

FROM python:3.10-slim AS poetry
RUN --mount=type=cache,target=/root/.cache <<EOF
  pip install poetry
EOF

FROM poetry AS builder
ADD . /app
WORKDIR /app
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN poetry install --only main --no-interaction

FROM python:3.10-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder --link /app /app
CMD ["atmosphere-operator"]
