# `orphan_delete`

The `orphan_delete` Ansible role provides a reusable mechanism to delete
Kubernetes resources (Deployments, StatefulSets, etc.) without removing
their underlying pods or workloads. It uses the `Orphan` propagation policy
to ensure that resources are deleted while leaving the pods in place, making
it ideal for scenarios like upgrading Helm charts where immutability of
certain fields (e.g., labels) can cause failures.
