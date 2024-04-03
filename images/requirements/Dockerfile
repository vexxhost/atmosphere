FROM ubuntu
ARG TARGETARCH
ARG TARGETVARIANT
RUN \
    --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT-var-cache-apt,sharing=locked,target=/var/cache/apt \
    --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT-var-lib-apt-lists,sharing=locked,target=/var/lib/apt/lists <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends ca-certificates git
EOF

ARG RELEASE
RUN <<EOF bash -xe
BRANCH=stable/${RELEASE}
if [ "${RELEASE}" = "master" ]; then
    BRANCH=master
fi

git clone --branch \$BRANCH https://github.com/openstack/requirements /src
EOF

RUN <<EOF sh -xe
sed -i 's/cryptography===36.0.2/cryptography===42.0.4/' /src/upper-constraints.txt
sed -i 's/cryptography===40.0.2/cryptography===42.0.4/' /src/upper-constraints.txt
sed -i 's/cryptography===41.0.7/cryptography===42.0.4/' /src/upper-constraints.txt
sed -i 's/Django===3.2.18/Django===3.2.24/' /src/upper-constraints.txt
sed -i 's/Flask===2.2.3/Flask===2.2.5/' /src/upper-constraints.txt
sed -i 's/Jinja2===3.1.2/Jinja2===3.1.3/' /src/upper-constraints.txt
sed -i 's/oauthlib===3.2.0/oauthlib===3.2.2/' /src/upper-constraints.txt
sed -i 's/paramiko===2.11.0/paramiko===3.4.0/' /src/upper-constraints.txt
sed -i 's/paramiko===3.1.0/paramiko===3.4.0/' /src/upper-constraints.txt
sed -i 's/protobuf===4.21.5/protobuf===4.21.6/' /src/upper-constraints.txt
sed -i 's/pyOpenSSL===22.0.0/pyOpenSSL===24.0.0/' /src/upper-constraints.txt
sed -i 's/pyOpenSSL===23.1.1/pyOpenSSL===24.0.0/' /src/upper-constraints.txt
sed -i 's/requests===2.28.1/requests===2.31.0/' /src/upper-constraints.txt
sed -i 's/requests===2.28.2/requests===2.31.0/' /src/upper-constraints.txt
sed -i 's/sqlparse===0.4.2/sqlparse===0.4.4/' /src/upper-constraints.txt
sed -i 's/urllib3===1.26.12/urllib3===1.26.18/' /src/upper-constraints.txt
sed -i 's/urllib3===1.26.15/urllib3===1.26.18/' /src/upper-constraints.txt
sed -i 's/Werkzeug===2.2.2/Werkzeug===2.3.8/' /src/upper-constraints.txt
sed -i 's/Werkzeug===2.2.3/Werkzeug===2.3.8/' /src/upper-constraints.txt
sed -i 's/zstd===1.5.2.5/zstd===1.5.4.0/' /src/upper-constraints.txt

sed -i '/glance-store/d' /src/upper-constraints.txt
sed -i '/horizon/d' /src/upper-constraints.txt
EOF
