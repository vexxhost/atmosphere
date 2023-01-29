local addAlerts = {
  prometheusAlerts+::
    {
      groups+: [
        {
          name: 'mysqld-extras',

          rules: [
            {
              alert: 'MysqlTooManyConnections',
              'for': '1m',
              expr: |||
                max_over_time(mysql_global_status_threads_connected[1m]) / mysql_global_variables_max_connections * 100 > 80
              |||,
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'MysqlHighThreadsRunning',
              'for': '1m',
              expr: |||
                max_over_time(mysql_global_status_threads_running[1m]) / mysql_global_variables_max_connections * 100 > 60
              |||,
              labels: {
                severity: 'warning',
              },
            },
            {
              alert: 'MysqlSlowQueries',
              'for': '2m',
              expr: |||
                increase(mysql_global_status_slow_queries[1m]) > 0
              |||,
              labels: {
                severity: 'warning',
              },
            },
          ],
        },
      ],
    },
};

{
  prometheusAlerts: {
    groups:
      (
        std.parseYaml(importstr 'vendor/github.com/prometheus/mysqld_exporter/mysqld-mixin/alerts/general.yaml').groups +
        std.parseYaml(importstr 'vendor/github.com/prometheus/mysqld_exporter/mysqld-mixin/alerts/galera.yaml').groups +
        std.parseYaml(importstr 'vendor/github.com/prometheus/mysqld_exporter/mysqld-mixin/rules/rules.yaml').groups
      ),
  },
} + addAlerts
