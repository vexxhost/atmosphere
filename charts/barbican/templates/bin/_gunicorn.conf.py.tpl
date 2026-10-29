#!/usr/bin/env python

# Copyright (c) 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Gunicorn config file.
References:
* https://docs.gunicorn.org/en/stable/configure.html
* https://docs.gunicorn.org/en/stable/settings.html
"""

{{- if .Values.wsgi.cpu_worker_ratio }}
import multiprocessing
workers = int(max(0, multiprocessing.cpu_count() * {{ .Values.wsgi.cpu_worker_ratio | float64 }}) + 1)
{{- end }}

preload_app = True
graceful_timeout = 80
reuse_port = True
