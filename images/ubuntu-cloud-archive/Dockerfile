FROM ubuntu
COPY trusted.gpg.d/* /etc/apt/trusted.gpg.d/

ARG RELEASE
RUN <<EOF bash -xe
source /etc/os-release

if [ "\${VERSION_CODENAME}" = "jammy" ]; then \
    if [ "${RELEASE}" = "yoga" ]; then \
        # NOTE: Yoga shipped with 22.04, so no need to add an extra repository.
        echo "" > /etc/apt/sources.list.d/cloudarchive.list; \
    elif [ "${RELEASE}" = "zed" ]; then \
        echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu \${VERSION_CODENAME}-updates/${RELEASE} main" > /etc/apt/sources.list.d/cloudarchive.list; \
    elif [ "${RELEASE}" = "2023.1" ]; then \
        echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu \${VERSION_CODENAME}-updates/antelope main" > /etc/apt/sources.list.d/cloudarchive.list; \
    elif [ "${RELEASE}" = "2023.2" ]; then \
        echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu \${VERSION_CODENAME}-updates/bobcat main" > /etc/apt/sources.list.d/cloudarchive.list; \
    elif [ "${RELEASE}" = "master" ]; then \
        echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu \${VERSION_CODENAME}-updates/caracal main" > /etc/apt/sources.list.d/cloudarchive.list; \
    else \
        echo "${RELEASE} is not supported on \${VERSION_CODENAME}"; \
        exit 1; \
    fi; \
else
    echo "Unsupported release"; \
    exit 1; \
fi
EOF
