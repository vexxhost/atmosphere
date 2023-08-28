local legacy = import 'legacy.libsonnet';

local ceph = import 'ceph.libsonnet';
local memcached = import 'vendor/github.com/grafana/jsonnet-libs/memcached-mixin/mixin.libsonnet';
local mysqld = import 'mysqld.libsonnet';
local node = import 'node.libsonnet';

local coredns = (import 'vendor/github.com/povilasv/coredns-mixin/mixin.libsonnet') + {
  _config+:: {
    corednsSelector: 'job="coredns"',
  },
};

{
  ceph: ceph.prometheusAlerts,
  coredns: coredns.prometheusAlerts,
  memcached: memcached.prometheusAlerts,
  'percona-xtradb-pxc': mysqld.prometheusAlerts,
  node: node.prometheusAlerts,
} + legacy
