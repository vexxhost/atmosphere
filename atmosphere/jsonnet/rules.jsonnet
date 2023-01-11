local legacy = import 'legacy.libsonnet';

local ceph = import 'ceph.libsonnet';
local mysqld = import 'mysqld.libsonnet';

local coredns = (import 'vendor/coredns-mixin/mixin.libsonnet') + {
  _config+:: {
    corednsSelector: 'job="coredns"',
  },
};

{
  ceph: ceph.prometheusAlerts,
  coredns: coredns.prometheusAlerts,
  'percona-xtradb-pxc': mysqld.prometheusAlerts,
} + legacy
