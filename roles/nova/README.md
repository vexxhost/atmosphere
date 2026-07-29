# `nova`

This role deploys the OpenStack Compute service using the vendored Nova Helm
chart. It configures the API, scheduler, and compute services used by the
deployment.
Configured flavors are created after the Compute API becomes available.
