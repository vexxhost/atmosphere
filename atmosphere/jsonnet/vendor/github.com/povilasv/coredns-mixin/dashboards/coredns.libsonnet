local grafana = import 'github.com/grafana/grafonnet-lib/grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local row = grafana.row;
local prometheus = grafana.prometheus;
local template = grafana.template;
local graphPanel = grafana.graphPanel;
local singlestat = grafana.singlestat;

{
  _config+:: {
    corednsSelector: 'job="kube-dns"',
  },

  grafanaDashboards+:: {
    'coredns.json':
      local upCount =
        singlestat.new(
          'Up',
          datasource='$datasource',
          span=1,
          valueName='min',
        )
        .addTarget(prometheus.target('sum(up{%(corednsSelector)s})' % $._config));

      local panicsCount =
        singlestat.new(
          'Panics',
          datasource='$datasource',
          span=1,
          valueName='max',
        )
        .addTarget(prometheus.target('sum(coredns_panics_total{%(corednsSelector)s})' % $._config));

      local rpcRate =
        graphPanel.new(
          'RPC Rate',
          datasource='$datasource',
          span=5,
          format='ops',
          min=0,
        )
        .addTarget(prometheus.target('sum(rate(coredns_dns_responses_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (rcode)' % $._config, legendFormat='{{rcode}}'))
        .addTarget(prometheus.target('sum(rate(coredns_forward_responses_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (rcode)' % $._config, legendFormat='forward {{rcode}}'));

      local requestDuration =
        graphPanel.new(
          'Request duration 99th quantile',
          datasource='$datasource',
          span=5,
          format='s',
          legend_show=true,
          legend_values=true,
          legend_current=true,
          legend_alignAsTable=true,
          legend_rightSide=true,
          min=0,
        )
        .addTarget(prometheus.target('histogram_quantile(0.99, sum(rate(coredns_dns_request_duration_seconds_bucket{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (server, zone, le))' % $._config, legendFormat='{{server}} {{zone}}'))
        .addTarget(prometheus.target('histogram_quantile(0.99, sum(rate(coredns_forward_request_duration_seconds_bucket{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (to, le))' % $._config, legendFormat='forward {{to}}'));

      local typeRate =
        graphPanel.new(
          'Requests (by qtype)',
          datasource='$datasource',
          span=4,
          format='ops',
          min=0,
        )
        .addTarget(prometheus.target('sum(rate(coredns_dns_requests_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (type)' % $._config, legendFormat='{{type}}'));

      local zoneRate =
        graphPanel.new(
          'Requests (by zone)',
          datasource='$datasource',
          span=4,
          format='ops',
          min=0,
        )
        .addTarget(prometheus.target('sum(rate(coredns_dns_requests_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (zone)' % $._config, legendFormat='{{zone}}'));

      local forwardRate =
        graphPanel.new(
          'Forward Requests (by to)',
          datasource='$datasource',
          span=4,
          format='ops',
          min=0,
        )
        .addTarget(prometheus.target('sum(rate(coredns_forward_requests_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (to)' % $._config, legendFormat='{{to}}'));

      local kubernetesDuration = if $._config.kubernetesPlugin then
        graphPanel.new(
          'Kubernetes DNS programming duration',
          datasource='$datasource',
          span=4,
          format='seconds',
          min=0,
        )
        .addTarget(prometheus.target('histogram_quantile(0.99, sum(rate(coredns_kubernetes_dns_programming_duration_seconds_bucket{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (service_kind, le))' % $._config, legendFormat='99th {{service_kind}}'))
        .addTarget(prometheus.target('histogram_quantile(0.50, sum(rate(coredns_kubernetes_dns_programming_duration_seconds_bucket{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (service_kind, le))' % $._config, legendFormat='50th {{service_kind}}'))
      else
        singlestat.new(
          'Plugins Enabled',
          datasource='$datasource',
          span=2,
          valueName='min',
        )
        .addTarget(prometheus.target('count(sum(coredns_plugin_enabled{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}) by (%(pluginNameLabel)s))' % $._config));

      local requestSize =
        graphPanel.new(
          'Request size',
          datasource='$datasource',
          span=if $._config.kubernetesPlugin then 4 else 5,
          format='bytes',
          min=0,
        )
        .addTarget(prometheus.target('histogram_quantile(0.99, sum(rate(coredns_dns_request_size_bytes_bucket{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (server, zone, proto, le))' % $._config, legendFormat='99th {{server}} {{zone}} {{proto}}'))
        .addTarget(prometheus.target('histogram_quantile(0.50, sum(rate(coredns_dns_request_size_bytes_bucket{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (server, zone, proto, le))' % $._config, legendFormat='50th {{server}} {{zone}} {{proto}}'));

      local responseSize =
        graphPanel.new(
          'Response size',
          datasource='$datasource',
          span=if $._config.kubernetesPlugin then 4 else 5,
          format='bytes',
          min=0,
        )
        .addTarget(prometheus.target('histogram_quantile(0.99, sum(rate(coredns_dns_response_size_bytes_bucket{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (server, zone, proto, le))' % $._config, legendFormat='99th {{server}} {{zone}} {{proto}}'))
        .addTarget(prometheus.target('histogram_quantile(0.50, sum(rate(coredns_dns_response_size_bytes_bucket{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (server, zone, proto, le))' % $._config, legendFormat='50th {{server}} {{zone}} {{proto}}'));

      local cachePercentage =
        singlestat.new(
          'Cached',
          datasource='$datasource',
          span=2,
          valueName='min',
          format='percentunit',
        )
        .addTarget(prometheus.target('sum(coredns_cache_hits_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}) / (sum(coredns_cache_misses_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}) + sum(coredns_cache_hits_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}))' % $._config));

      local cacheRate =
        graphPanel.new(
          'Cache hit Rate',
          datasource='$datasource',
          span=5,
          format='ops',
          min=0,
        )
        .addTarget(prometheus.target('sum(rate(coredns_cache_hits_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])) by (type)' % $._config, legendFormat='{{type}}'))
        .addTarget(prometheus.target('sum(rate(coredns_cache_misses_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m]))' % $._config, legendFormat='misses'));

      local cacheSize =
        graphPanel.new(
          'Cache Size',
          datasource='$datasource',
          span=5,
          format='short',
          min=0,
        )
        .addTarget(prometheus.target('sum(coredns_cache_entries{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}) by (type)' % $._config, legendFormat='{{type}}'));

      local memory =
        graphPanel.new(
          'Memory',
          datasource='$datasource',
          span=4,
          format='bytes',
          min=0,
        )
        .addTarget(prometheus.target('process_resident_memory_bytes{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}' % $._config, legendFormat='{{%(instanceLabel)s}}' % $._config));

      local cpu =
        graphPanel.new(
          'CPU usage',
          datasource='$datasource',
          span=4,
          format='short',
          min=0,
        )
        .addTarget(prometheus.target('rate(process_cpu_seconds_total{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}[5m])' % $._config, legendFormat='{{%(instanceLabel)s}}' % $._config));

      local goroutines =
        graphPanel.new(
          'Goroutines',
          datasource='$datasource',
          span=4,
          format='short',
          min=0,
        )
        .addTarget(prometheus.target('go_goroutines{%(corednsSelector)s,%(instanceLabel)s=~"$instance"}' % $._config, legendFormat='{{%(instanceLabel)s}}' % $._config));


      dashboard.new(
        '%(dashboardNamePrefix)sCoreDNS' % $._config.grafana,
        time_from='now-1h',
        uid=($._config.grafanaDashboardIDs['coredns.json']),
        tags=($._config.grafana.dashboardTags),
      ).addTemplate(
        {
          current: {
            text: 'default',
            value: 'default',
          },
          hide: 0,
          label: 'Data Source',
          name: 'datasource',
          options: [],
          query: 'prometheus',
          refresh: 1,
          regex: '',
          type: 'datasource',
        },
      ).addTemplate(
        template.new(
          'instance',
          '$datasource',
          'label_values(coredns_build_info{%(corednsSelector)s}, %(instanceLabel)s)' % $._config,
          refresh='time',
          includeAll=true,
          sort=1,
        )
      ).addRow(
        row.new()
        .addPanel(upCount)
        .addPanel(panicsCount)
        .addPanel(rpcRate)
        .addPanel(requestDuration)
      ).addRow(
        row.new()
        .addPanel(typeRate)
        .addPanel(zoneRate)
        .addPanel(forwardRate)
      ).addRow(
        row.new()
        .addPanel(cachePercentage)
        .addPanel(cacheRate)
        .addPanel(cacheSize)
      ).addRow(
        row.new()
        .addPanel(kubernetesDuration)
        .addPanel(requestSize)
        .addPanel(responseSize)
      ).addRow(
        row.new()
        .addPanel(memory)
        .addPanel(cpu)
        .addPanel(goroutines)
      ) + { refresh: $._config.grafana.refresh },
  },
}
