FROM ubuntu
LABEL org.opencontainers.image.source=https://github.com/vexxhost/atmosphere
RUN <<EOF
rm -f /etc/apt/apt.conf.d/docker-clean
echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
EOF

# ARG TARGETARCH
# ARG TARGETVARIANT
# RUN \
#     --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT-var-cache-apt,sharing=locked,target=/var/cache/apt \
#     --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT-var-lib-apt-lists,sharing=locked,target=/var/lib/apt/lists <<EOF bash -xe
# apt-get update -qq
# apt-get install -qq -y --no-install-recommends \
#     # CVE-XXXX
# EOF
