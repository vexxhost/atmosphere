# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

FROM alpine/git:v2.47.2 AS clone
COPY --from=git / /src
RUN --mount=type=bind,from=patches,source=/,target=/patches <<EOF sh -xe
git -C /src apply --verbose /patches/*
EOF

FROM scratch
COPY --from=clone /src /
