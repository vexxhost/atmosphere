# `magnum_kubeconfig`

This role allows you to retrieve the `KUBECONFIG` file for a specific cluster,
it exists because of a Magnum bug that enforces that you're in the same project
in order to be able to pull the configuration.
