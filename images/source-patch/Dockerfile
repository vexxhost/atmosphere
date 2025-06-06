# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

FROM alpine/git:v2.47.2 AS shallow-clone
COPY --from=git / /src
RUN --mount=type=bind,from=patches,source=/,target=/patches <<EOF sh -xe
git -C /src apply --verbose /patches/*
EOF

FROM shallow-clone AS clone
RUN git -C /src fetch --unshallow

FROM scratch AS unshallow
COPY --from=clone /src /

FROM scratch
COPY --from=shallow-clone /src /
