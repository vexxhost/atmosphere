{
  prometheusAlerts+: {
    groups+: [
      {
        name: 'libvirt',
        rules:
          local dropAlert(direction) =
            local capitalized = std.asciiUpper(std.substr(direction, 0, 1)) + std.substr(direction, 1, std.length(direction) - 1);
            local alertName = 'LibvirtDomainInterface' + capitalized + 'Drops';
            {
              alert: alertName,
              expr: 'increase(libvirt_domain_interface_stats_' + direction + '_drops_total[5m]) > 0',
              'for': '5m',
              labels: {
                severity: 'P3',
              },
              annotations: {
                summary: 'Libvirt: virtual machine network interface dropping ' + direction + ' packets',
                description: 'Domain {{ $labels.domain }} interface {{ $labels.target_device }} has dropped {{ $value }} ' + direction + ' packets in the last 5 minutes. Sustained packet drops can degrade tenant connectivity. Normal behavior is zero drops.',
                runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#' + std.asciiLower(alertName),
              },
            };
          [
            dropAlert('receive'),
            dropAlert('transmit'),
          ],
      },
    ],
  },
}
