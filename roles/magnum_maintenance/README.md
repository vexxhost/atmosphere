# `magnum_cluster_maintenance`

This is an operational role that allows you to place a Magnum cluster in a
maintenance mode.   It will disable both the auto-healer and the auto-scaler
which should bring the cluster to a static state.

The only thing that stays running is the OpenStack Cloud Controller but that
should not be a problem.
