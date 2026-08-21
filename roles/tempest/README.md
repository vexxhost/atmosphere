# `tempest`

This role deploys the Tempest chart and runs the configured test selection.
For the `ovn` molecule scenario, it extends the default smoke coverage with
the Neutron FWaaS v2 API tests so `molecule aio verify` exercises the FWaaS
API wiring.
