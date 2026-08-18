{
  prometheusAlerts+:: {
    groups: [
      {
        name: 'libvirt',
        rules: [
          {
            alert: 'LibvirtPodRestarts',
            expr: |||
              sum by (node) (
                increase(kube_pod_container_status_restarts_total{namespace="openstack", pod=~"libvirt-.+", container="libvirt"}[1h])
                * on(namespace, pod) group_left(node)
                max by (namespace, pod, node) (
                  kube_pod_info{namespace="openstack", pod=~"libvirt-.+"}
                )
              ) > 3
            |||,
            'for': '15m',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Libvirt: repeated pod restarts may cause stale mounts on {{ $labels.node }}',
              description: 'The expression based on increase(kube_pod_container_status_restarts_total[1h]) reports {{ $value }} libvirt container restarts on {{ $labels.node }} in the last hour, which exceeds the threshold of 3. Normal behavior is zero or only rare libvirt restarts. Repeated restarts can recreate Kubernetes subPath bind mounts under /etc/ceph and may lead to stale host mounts.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#libvirtpodrestarts',
            },
          },
        ],
      },
    ],
  },
}
