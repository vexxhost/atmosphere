{
  prometheusAlerts+: {
    groups+: [
      {
        name: 'smartctl-health',
        rules: [
          {
            alert: 'SmartctlDiskUnhealthy',
            expr: 'smartctl_device_smart_status == 0',
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'Disk: SMART overall health check failed',
              description: 'The SMART overall-health self-assessment for disk {{ $labels.device }} on node {{ $labels.instance }} is reporting failure (smartctl_device_smart_status=0). The drive firmware predicts imminent failure. Normal value is 1.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskunhealthy',
            },
          },
          {
            alert: 'SmartctlDiskCriticalWarning',
            expr: 'smartctl_device_critical_warning != 0',
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'Disk: NVMe critical warning bit set',
              description: 'The NVMe critical_warning bitfield for disk {{ $labels.device }} on node {{ $labels.instance }} is {{ $value }} (normal is 0). Bits indicate available spare below threshold, temperature above critical, NVM subsystem reliability degraded, media in read-only mode, or volatile memory backup failed.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskcriticalwarning',
            },
          },
          {
            alert: 'SmartctlDiskAvailableSpareLow',
            expr: 'smartctl_device_available_spare < smartctl_device_available_spare_threshold',
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'Disk: NVMe available spare below manufacturer threshold',
              description: 'The NVMe available spare on disk {{ $labels.device }} on node {{ $labels.instance }} is {{ $value }}%, which is below the manufacturer-defined threshold. The drive has nearly exhausted its reserve blocks; failure is imminent. Normal is well above the threshold (typically 100% on a healthy drive).',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskavailablesparelow',
            },
          },
          {
            alert: 'SmartctlDiskWearoutCritical',
            expr: 'smartctl_device_percentage_used > 90',
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Disk: NVMe wear level critical',
              description: 'The NVMe disk {{ $labels.device }} on node {{ $labels.instance }} reports {{ $value }}% of its rated endurance used (smartctl_device_percentage_used), exceeding the 90% threshold. Plan immediate replacement. Normal operating range is below 75%. (NVMe-only; SATA drives are covered by SmartctlDiskAttributeFailing.)',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskwearoutcritical',
            },
          },
          {
            alert: 'SmartctlDiskAttributeFailing',
            expr: '(smartctl_device_attribute{attribute_value_type="value"} <= on(instance, device, attribute_id) smartctl_device_attribute{attribute_value_type="thresh"}) and on(instance, device, attribute_id) (smartctl_device_attribute{attribute_value_type="thresh"} > 0)',
            'for': '5m',
            labels: {
              severity: 'P2',
            },
            annotations: {
              summary: 'Disk: SMART attribute below failure threshold',
              description: 'The SMART attribute {{ $labels.attribute_name }} (id {{ $labels.attribute_id }}) on disk {{ $labels.device }} on node {{ $labels.instance }} has dropped to a normalized value of {{ $value }}, at or below the threshold the drive firmware uses to declare the attribute failing. Normal is for the value to stay well above its threshold. The drive itself is signalling imminent failure of this attribute (e.g., wear-leveling, reallocation, or a vendor-specific prefailure indicator).',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskattributefailing',
            },
          },
          {
            alert: 'SmartctlDiskScsiUncorrectedErrors',
            expr: 'increase(smartctl_read_total_uncorrected_errors[24h]) > 0 or increase(smartctl_write_total_uncorrected_errors[24h]) > 0',
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Disk: SCSI/SAS uncorrected I/O errors',
              description: 'The SCSI/SAS disk {{ $labels.device }} on node {{ $labels.instance }} accumulated {{ $value }} new uncorrected read/write errors in the last 24 hours. Normal is zero growth: any non-zero increase indicates the drive could not recover I/O via on-disk ECC, which means data loss or imminent failure.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskscsiuncorrectederrors',
            },
          },
          {
            alert: 'SmartctlDiskPendingSectorsGrowing',
            expr: 'increase(smartctl_device_attribute{attribute_id="197",attribute_value_type="raw"}[24h]) > 0',
            'for': '1h',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Disk: pending sector count growing',
              description: 'The SATA disk {{ $labels.device }} on node {{ $labels.instance }} added {{ $value }} sectors awaiting reallocation in the last 24 hours (Current_Pending_Sector, attribute 197). Normal is zero growth: a stable non-zero count is harmless (those sectors will be remapped on next write), but ongoing growth indicates active media degradation.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskpendingsectorsgrowing',
            },
          },
          {
            alert: 'SmartctlDiskUncorrectableSectorsGrowing',
            expr: 'increase(smartctl_device_attribute{attribute_id="198",attribute_value_type="raw"}[24h]) > 0',
            'for': '1h',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Disk: uncorrectable sector count growing',
              description: 'The SATA disk {{ $labels.device }} on node {{ $labels.instance }} added {{ $value }} offline-uncorrectable sectors in the last 24 hours (Offline_Uncorrectable, attribute 198). Normal is zero growth: a stable non-zero count is harmless, but ongoing growth indicates confirmed unrecoverable data loss in newly affected LBAs.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskuncorrectablesectorsgrowing',
            },
          },
          {
            alert: 'SmartctlDiskMediaErrorsGrowing',
            expr: 'increase(smartctl_device_media_errors[24h]) > 0',
            'for': '15m',
            labels: {
              severity: 'P3',
            },
            annotations: {
              summary: 'Disk: NVMe media errors increasing',
              description: 'The NVMe disk {{ $labels.device }} on node {{ $labels.instance }} accumulated {{ $value }} new media errors in the last 24 hours (smartctl_device_media_errors). Normal is zero growth over time. New errors indicate active uncorrectable ECC failures or LBA tag mismatches.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskmediaerrorsgrowing',
            },
          },
          {
            alert: 'SmartctlDiskWearoutWarning',
            expr: 'smartctl_device_percentage_used > 75',
            'for': '1h',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Disk: NVMe wear level elevated',
              description: 'The NVMe disk {{ $labels.device }} on node {{ $labels.instance }} reports {{ $value }}% of its rated endurance used (smartctl_device_percentage_used), exceeding the 75% threshold. Plan replacement during the next maintenance window. Normal operating range is below 75%. (NVMe-only; SATA drives are covered by SmartctlDiskAttributeFailing.)',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskwearoutwarning',
            },
          },
          {
            alert: 'SmartctlDiskScsiGrownDefectsGrowing',
            expr: 'increase(smartctl_scsi_grown_defect_list[24h]) > 0',
            'for': '1h',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Disk: SCSI/SAS grown defect list growing',
              description: 'The SCSI/SAS disk {{ $labels.device }} on node {{ $labels.instance }} added {{ $value }} entries to its grown defect list in the last 24 hours. Normal is zero growth: a stable non-zero count is harmless, but ongoing growth means the drive is actively reallocating bad blocks.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskscsigrowndefectsgrowing',
            },
          },
          {
            alert: 'SmartctlDiskTemperatureHigh',
            expr: 'smartctl_device_temperature{temperature_type="current"} > 65',
            'for': '1h',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Disk: temperature sustained high',
              description: 'The disk {{ $labels.device }} on node {{ $labels.instance }} has run at {{ $value }}°C for over an hour, exceeding the 65°C threshold. Normal operating temperature is below 50°C for HDDs and below 60°C for SSDs. Check chassis cooling and airflow.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldisktemperaturehigh',
            },
          },
          {
            alert: 'SmartctlDiskReallocatedSectorsGrowing',
            expr: 'increase(smartctl_device_attribute{attribute_id="5",attribute_value_type="raw"}[24h]) > 0',
            'for': '1h',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Disk: reallocated sector count growing',
              description: 'The SATA disk {{ $labels.device }} on node {{ $labels.instance }} reallocated {{ $value }} additional sectors in the last 24 hours (Reallocated_Sector_Ct, attribute 5). Normal is zero growth: a stable non-zero count is harmless, but ongoing reallocation indicates active media degradation.',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskreallocatedsectorsgrowing',
            },
          },
          {
            alert: 'SmartctlDiskSelfTestFailed',
            expr: 'smartctl_device_self_test_log_error_count > 0',
            'for': '1h',
            labels: {
              severity: 'P4',
            },
            annotations: {
              summary: 'Disk: SATA SMART self-test reported errors',
              description: 'The SATA disk {{ $labels.device }} on node {{ $labels.instance }} has {{ $value }} entries in its SMART self-test error log (self_test_log_type={{ $labels.self_test_log_type }}). Normal is 0. Even one failed self-test indicates the drive could not complete an internal integrity check. (SATA-only; the upstream exporter does not surface NVMe self-test results.)',
              runbook_url: 'https://vexxhost.github.io/atmosphere/admin/monitoring.html#smartctldiskselftestfailed',
            },
          },
        ],
      },
    ],
  },
}
