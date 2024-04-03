FROM git AS barbican
ARG BARBICAN_GIT_REF
ADD --keep-git-dir=true https://opendev.org/openstack/barbican.git#${BARBICAN_GIT_REF} /src
RUN git fetch --unshallow

FROM openstack-venv-builder AS build
COPY --from=barbican --link /src /src/barbican
ARG TARGETARCH
ARG TARGETVARIANT
RUN \
    --mount=type=cache,id=pip-$TARGETARCH$TARGETVARIANT-$RELEASE-cache,sharing=locked,target=/root/.cache/pip <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/barbican \
        pykmip
EOF

FROM openstack-runtime
COPY --from=build --link /var/lib/openstack /var/lib/openstack
