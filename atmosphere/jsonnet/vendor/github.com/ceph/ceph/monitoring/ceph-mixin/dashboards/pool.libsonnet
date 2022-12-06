local g = import 'grafonnet/grafana.libsonnet';

(import 'utils.libsonnet') {
  'pool-overview.json':
    $.dashboardSchema(
      'Ceph Pools Overview',
      '',
      'z99hzWtmk',
      'now-1h',
      '30s',
      22,
      $._config.dashboardTags,
      ''
    )
    .addAnnotation(
      $.addAnnotationSchema(
        1,
        '-- Grafana --',
        true,
        true,
        'rgba(0, 211, 255, 1)',
        'Annotations & Alerts',
        'dashboard'
      )
    )
    .addTemplate(
      g.template.datasource('datasource', 'prometheus', 'default', label='Data Source')
    )
    .addTemplate(
      $.addClusterTemplate()
    )
    .addTemplate(
      $.addJobTemplate()
    )
    .addTemplate(
      g.template.custom(label='TopK',
                        name='topk',
                        current='15',
                        query='15')
    )
    .addPanels([
      $.simpleSingleStatPanel(
        'none',
        'Pools',
        '',
        'avg',
        'count(ceph_pool_metadata{%(matchers)s})' % $.matchers(),
        true,
        'table',
        0,
        0,
        3,
        3
      ),
      $.simpleSingleStatPanel(
        'none',
        'Pools with Compression',
        'Count of the pools that have compression enabled',
        'current',
        'count(ceph_pool_metadata{%(matchers)s, compression_mode!="none"})' % $.matchers(),
        null,
        '',
        3,
        0,
        3,
        3
      ),
      $.simpleSingleStatPanel(
        'bytes',
        'Total Raw Capacity',
        'Total raw capacity available to the cluster',
        'current',
        'sum(ceph_osd_stat_bytes{%(matchers)s})' % $.matchers(),
        null,
        '',
        6,
        0,
        3,
        3
      ),
      $.simpleSingleStatPanel(
        'bytes',
        'Raw Capacity Consumed',
        'Total raw capacity consumed by user data and associated overheads (metadata + redundancy)',
        'current',
        'sum(ceph_pool_bytes_used{%(matchers)s})' % $.matchers(),
        true,
        '',
        9,
        0,
        3,
        3
      ),
      $.simpleSingleStatPanel(
        'bytes',
        'Logical Stored ',
        'Total of client data stored in the cluster',
        'current',
        'sum(ceph_pool_stored{%(matchers)s})' % $.matchers(),
        true,
        '',
        12,
        0,
        3,
        3
      ),
      $.simpleSingleStatPanel(
        'bytes',
        'Compression Savings',
        'A compression saving is determined as the data eligible to be compressed minus the capacity used to store the data after compression',
        'current',
        |||
          sum(
            ceph_pool_compress_under_bytes{%(matchers)s} -
              ceph_pool_compress_bytes_used{%(matchers)s}
          )
        ||| % $.matchers(),
        null,
        '',
        15,
        0,
        3,
        3
      ),
      $.simpleSingleStatPanel(
        'percent',
        'Compression Eligibility',
        'Indicates how suitable the data is within the pools that are/have been enabled for compression - averaged across all pools holding compressed data',
        'current',
        |||
          (
            sum(ceph_pool_compress_under_bytes{%(matchers)s} > 0) /
              sum(ceph_pool_stored_raw{%(matchers)s} and ceph_pool_compress_under_bytes{%(matchers)s} > 0)
          ) * 100
        ||| % $.matchers(),
        null,
        'table',
        18,
        0,
        3,
        3
      ),
      $.simpleSingleStatPanel(
        'none',
        'Compression Factor',
        'This factor describes the average ratio of data eligible to be compressed divided by the data actually stored. It does not account for data written that was ineligible for compression (too small, or compression yield too low)',
        'current',
        |||
          sum(
            ceph_pool_compress_under_bytes{%(matchers)s} > 0)
              / sum(ceph_pool_compress_bytes_used{%(matchers)s} > 0
          )
        ||| % $.matchers(),
        null,
        '',
        21,
        0,
        3,
        3
      ),
      $.addTableSchema(
        '$datasource',
        '',
        { col: 5, desc: true },
        [
          $.overviewStyle('', 'Time', 'hidden', 'short'),
          $.overviewStyle('', 'instance', 'hidden', 'short'),
          $.overviewStyle('', 'job', 'hidden', 'short'),
          $.overviewStyle('Pool Name', 'name', 'string', 'short'),
          $.overviewStyle('Pool ID', 'pool_id', 'hidden', 'none'),
          $.overviewStyle('Compression Factor', 'Value #A', 'number', 'none'),
          $.overviewStyle('% Used', 'Value #D', 'number', 'percentunit', 'value', ['70', '85']),
          $.overviewStyle('Usable Free', 'Value #B', 'number', 'bytes'),
          $.overviewStyle('Compression Eligibility', 'Value #C', 'number', 'percent'),
          $.overviewStyle('Compression Savings', 'Value #E', 'number', 'bytes'),
          $.overviewStyle('Growth (5d)', 'Value #F', 'number', 'bytes', 'value', ['0', '0']),
          $.overviewStyle('IOPS', 'Value #G', 'number', 'none'),
          $.overviewStyle('Bandwidth', 'Value #H', 'number', 'Bps'),
          $.overviewStyle('', '__name__', 'hidden', 'short'),
          $.overviewStyle('', 'type', 'hidden', 'short'),
          $.overviewStyle('', 'compression_mode', 'hidden', 'short'),
          $.overviewStyle('Type', 'description', 'string', 'short'),
          $.overviewStyle('Stored', 'Value #J', 'number', 'bytes'),
          $.overviewStyle('', 'Value #I', 'hidden', 'short'),
          $.overviewStyle('Compression', 'Value #K', 'string', 'short', null, [], [{ text: 'ON', value: '1' }]),
        ],
        'Pool Overview',
        'table'
      )
      .addTargets(
        [
          $.addTargetSchema(
            |||
              (
                ceph_pool_compress_under_bytes{%(matchers)s} /
                  ceph_pool_compress_bytes_used{%(matchers)s} > 0
              ) and on(pool_id) (
                (
                  (ceph_pool_compress_under_bytes{%(matchers)s} > 0) /
                    ceph_pool_stored_raw{%(matchers)s}
                ) * 100 > 0.5
              )
            ||| % $.matchers(),
            'A',
            'table',
            1,
            true
          ),
          $.addTargetSchema(
            |||
              ceph_pool_max_avail{%(matchers)s} *
                on(pool_id) group_left(name) ceph_pool_metadata{%(matchers)s}
            ||| % $.matchers(),
            'B',
            'table',
            1,
            true
          ),
          $.addTargetSchema(
            |||
              (
                (ceph_pool_compress_under_bytes{%(matchers)s} > 0) /
                  ceph_pool_stored_raw{%(matchers)s}
              ) * 100
            ||| % $.matchers(),
            'C',
            'table',
            1,
            true
          ),
          $.addTargetSchema(
            |||
              ceph_pool_percent_used{%(matchers)s} *
                on(pool_id) group_left(name) ceph_pool_metadata{%(matchers)s}
            ||| % $.matchers(),
            'D',
            'table',
            1,
            true
          ),
          $.addTargetSchema(
            |||
              ceph_pool_compress_under_bytes{%(matchers)s} -
                ceph_pool_compress_bytes_used{%(matchers)s} > 0
            ||| % $.matchers(),
            'E',
            'table',
            1,
            true
          ),
          $.addTargetSchema(
            'delta(ceph_pool_stored{%(matchers)s}[5d])' % $.matchers(), 'F', 'table', 1, true
          ),
          $.addTargetSchema(
            |||
              rate(ceph_pool_rd{%(matchers)s}[$__rate_interval])
                + rate(ceph_pool_wr{%(matchers)s}[$__rate_interval])
            ||| % $.matchers(),
            'G',
            'table',
            1,
            true
          ),
          $.addTargetSchema(
            |||
              rate(ceph_pool_rd_bytes{%(matchers)s}[$__rate_interval]) +
                rate(ceph_pool_wr_bytes{%(matchers)s}[$__rate_interval])
            ||| % $.matchers(),
            'H',
            'table',
            1,
            true
          ),
          $.addTargetSchema(
            'ceph_pool_metadata{%(matchers)s}' % $.matchers(), 'I', 'table', 1, true
          ),
          $.addTargetSchema(
            'ceph_pool_stored{%(matchers)s} * on(pool_id) group_left ceph_pool_metadata{%(matchers)s}' % $.matchers(),
            'J',
            'table',
            1,
            true
          ),
          $.addTargetSchema(
            'ceph_pool_metadata{%(matchers)s, compression_mode!="none"}' % $.matchers(), 'K', 'table', 1, true
          ),
          $.addTargetSchema('', 'L', '', '', null),
        ]
      ) + { gridPos: { x: 0, y: 3, w: 24, h: 6 } },
      $.simpleGraphPanel(
        {},
        'Top $topk Client IOPS by Pool',
        'This chart shows the sum of read and write IOPS from all clients by pool',
        'short',
        'IOPS',
        0,
        |||
          topk($topk,
            round(
              (
                rate(ceph_pool_rd{%(matchers)s}[$__rate_interval]) +
                  rate(ceph_pool_wr{%(matchers)s}[$__rate_interval])
              ), 1
            ) * on(pool_id) group_left(instance,name) ceph_pool_metadata{%(matchers)s})
        ||| % $.matchers(),
        '{{name}} ',
        0,
        9,
        12,
        8
      )
      .addTarget(
        $.addTargetSchema(
          |||
            topk($topk,
              rate(ceph_pool_wr{%(matchers)s}[$__rate_interval]) +
                on(pool_id) group_left(instance,name) ceph_pool_metadata{%(matchers)s}
            )
          ||| % $.matchers(),
          '{{name}} - write'
        )
      ),
      $.simpleGraphPanel(
        {},
        'Top $topk Client Bandwidth by Pool',
        'The chart shows the sum of read and write bytes from all clients, by pool',
        'Bps',
        'Throughput',
        0,
        |||
          topk($topk,
            (
              rate(ceph_pool_rd_bytes{%(matchers)s}[$__rate_interval]) +
                rate(ceph_pool_wr_bytes{%(matchers)s}[$__rate_interval])
            ) * on(pool_id) group_left(instance, name) ceph_pool_metadata{%(matchers)s}
          )
        ||| % $.matchers(),
        '{{name}}',
        12,
        9,
        12,
        8
      ),
      $.simpleGraphPanel(
        {},
        'Pool Capacity Usage (RAW)',
        'Historical view of capacity usage, to help identify growth and trends in pool consumption',
        'bytes',
        'Capacity Used',
        0,
        'ceph_pool_bytes_used{%(matchers)s} * on(pool_id) group_right ceph_pool_metadata{%(matchers)s}' % $.matchers(),
        '{{name}}',
        0,
        17,
        24,
        7
      ),
    ]),
  'pool-detail.json':
    $.dashboardSchema(
      'Ceph Pool Details',
      '',
      '-xyV8KCiz',
      'now-1h',
      '30s',
      22,
      $._config.dashboardTags,
      ''
    )
    .addRequired(
      type='grafana', id='grafana', name='Grafana', version='5.3.2'
    )
    .addRequired(
      type='panel', id='graph', name='Graph', version='5.0.0'
    )
    .addRequired(
      type='panel', id='singlestat', name='Singlestat', version='5.0.0'
    )
    .addAnnotation(
      $.addAnnotationSchema(
        1,
        '-- Grafana --',
        true,
        true,
        'rgba(0, 211, 255, 1)',
        'Annotations & Alerts',
        'dashboard'
      )
    )
    .addTemplate(
      g.template.datasource('datasource', 'prometheus', 'default', label='Data Source')
    )
    .addTemplate(
      $.addClusterTemplate()
    )
    .addTemplate(
      $.addJobTemplate()
    )
    .addTemplate(
      $.addTemplateSchema('pool_name',
                          '$datasource',
                          'label_values(ceph_pool_metadata{%(matchers)s}, name)' % $.matchers(),
                          1,
                          false,
                          1,
                          'Pool Name',
                          '')
    )
    .addPanels([
      $.gaugeSingleStatPanel(
        'percentunit',
        'Capacity used',
        '',
        'current',
        true,
        1,
        true,
        true,
        '.7,.8',
        |||
          (ceph_pool_stored{%(matchers)s} / (ceph_pool_stored{%(matchers)s} + ceph_pool_max_avail{%(matchers)s})) *
            on(pool_id) group_left(instance, name) ceph_pool_metadata{%(matchers)s, name=~"$pool_name"}
        ||| % $.matchers(),
        'time_series',
        0,
        0,
        7,
        7
      ),
      $.gaugeSingleStatPanel(
        's',
        'Time till full',
        'Time till pool is full assuming the average fill rate of the last 6 hours',
        false,
        100,
        false,
        false,
        '',
        'current',
        |||
          (ceph_pool_max_avail{%(matchers)s} / deriv(ceph_pool_stored{%(matchers)s}[6h])) *
            on(pool_id) group_left(instance, name) ceph_pool_metadata{%(matchers)s, name=~"$pool_name"} > 0
        ||| % $.matchers(),
        'time_series',
        7,
        0,
        5,
        7
      ),
      $.simpleGraphPanel(
        {
          read_op_per_sec:
            '#3F6833',
          write_op_per_sec: '#E5AC0E',
        },
        '$pool_name Object Ingress/Egress',
        '',
        'ops',
        'Objects out(-) / in(+) ',
        null,
        |||
          deriv(ceph_pool_objects{%(matchers)s}[1m]) *
            on(pool_id) group_left(instance, name) ceph_pool_metadata{%(matchers)s, name=~"$pool_name"}
        ||| % $.matchers(),
        'Objects per second',
        12,
        0,
        12,
        7
      ),
      $.simpleGraphPanel(
        {
          read_op_per_sec: '#3F6833',
          write_op_per_sec: '#E5AC0E',
        },
        '$pool_name Client IOPS',
        '',
        'iops',
        'Read (-) / Write (+)',
        null,
        |||
          rate(ceph_pool_rd{%(matchers)s}[$__rate_interval]) *
            on(pool_id) group_left(instance,name) ceph_pool_metadata{%(matchers)s, name=~"$pool_name"}
        ||| % $.matchers(),
        'reads',
        0,
        7,
        12,
        7
      )
      .addSeriesOverride({ alias: 'reads', transform: 'negative-Y' })
      .addTarget(
        $.addTargetSchema(
          |||
            rate(ceph_pool_wr{%(matchers)s}[$__rate_interval]) *
              on(pool_id) group_left(instance, name) ceph_pool_metadata{%(matchers)s, name=~"$pool_name"}
          ||| % $.matchers(),
          'writes'
        )
      ),
      $.simpleGraphPanel(
        {
          read_op_per_sec: '#3F6833',
          write_op_per_sec: '#E5AC0E',
        },
        '$pool_name Client Throughput',
        '',
        'Bps',
        'Read (-) / Write (+)',
        null,
        |||
          rate(ceph_pool_rd_bytes{%(matchers)s}[$__rate_interval]) +
            on(pool_id) group_left(instance, name) ceph_pool_metadata{%(matchers)s, name=~"$pool_name"}
        ||| % $.matchers(),
        'reads',
        12,
        7,
        12,
        7
      )
      .addSeriesOverride({ alias: 'reads', transform: 'negative-Y' })
      .addTarget(
        $.addTargetSchema(
          |||
            rate(ceph_pool_wr_bytes{%(matchers)s}[$__rate_interval]) +
              on(pool_id) group_left(instance,name) ceph_pool_metadata{%(matchers)s, name=~"$pool_name"}
          ||| % $.matchers(),
          'writes'
        )
      ),
      $.simpleGraphPanel(
        {
          read_op_per_sec: '#3F6833',
          write_op_per_sec: '#E5AC0E',
        },
        '$pool_name Objects',
        '',
        'short',
        'Objects',
        null,
        |||
          ceph_pool_objects{%(matchers)s} *
            on(pool_id) group_left(instance,name) ceph_pool_metadata{%(matchers)s, name=~"$pool_name"}
        ||| % $.matchers(),
        'Number of Objects',
        0,
        14,
        12,
        7
      ),
    ]),
}
