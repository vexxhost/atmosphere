# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import pbr.version

__version__ = pbr.version.VersionInfo("atmosphere").release_string()
