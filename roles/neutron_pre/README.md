# `neutron_pre`

This role installs the Neutron Helm chart and creates the network
ingress. Under the parallel deploy orchestrator it runs in parallel with
the main `neutron` role so the heavy Helm install does not block on
Nova. Only the post-install "Create networks" task (which hits the
neutron-server AZ check that requires the `nova` availability zone)
remains gated on Nova in the main `neutron` role.
