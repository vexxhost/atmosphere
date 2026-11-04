# `tempest`

This role deploys the Tempest chart and runs the configured test selection.
For ML2/OVN deployments, it extends the default smoke coverage with the
Neutron FWaaS v2 API tests. This selection applies whenever the Tempest
playbook runs with ML2/OVN, including `molecule aio verify`.
