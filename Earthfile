VERSION 0.7
FROM python:3.10

poetry:
  RUN pip3 install poetry

deps:
  FROM +poetry
  COPY pyproject.toml poetry.lock ./
  RUN poetry export -f requirements.txt --without-hashes > requirements.txt
  RUN pip wheel -r requirements.txt --wheel-dir=/wheels
  SAVE ARTIFACT requirements.txt
  SAVE ARTIFACT /wheels

build:
  FROM +deps
  RUN python3 -m venv /venv
  ENV PATH=/venv/bin:$PATH
  RUN pip install -r requirements.txt
  SAVE ARTIFACT /venv

docker:
  COPY +build/venv /venv
  ENV PATH=/venv/bin:$PATH

pin-images:
  FROM +docker
  COPY roles/defaults/defaults/main.yml /defaults.yml
  COPY build/pin-images.py /usr/local/bin/pin-images
  RUN /usr/local/bin/pin-images /defaults.yml /pinned.yml
  SAVE ARTIFACT /pinned.yml AS LOCAL roles/defaults/defaults/main.yml
