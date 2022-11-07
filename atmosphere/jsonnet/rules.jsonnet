local legacy = import 'legacy.libsonnet';

local ceph = import 'ceph.libsonnet';
local mysqld = import 'mysqld.libsonnet';
local coredns = import 'vendor/coredns-mixin/mixin.libsonnet';
local memcached = import 'vendor/memcached-mixin/mixin.libsonnet';

{
  ceph: ceph.prometheusAlerts,
  coredns: coredns.prometheusAlerts,
  memcached: memcached.prometheusAlerts,
  'percona-xtradb-pxc': mysqld.prometheusAlerts,
} + legacy
