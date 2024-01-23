# Monitoring

## Creating silences

In order to create a silence, you'll need to login to your Grafana instance that
is deployed as part of Atmosphere as an admin user.

1. Click on the hamburger menu in the top left corner and select "Alerting"
   and then "Silences" from the menu.

   ![Silences menu](static/monitoring-silences-menu.png)

2. Ensure that you select "AlertManager" on the top right corner of the page,
   this will make sure that you create a silence inside of the AlertManager
   that is managed by the Prometheus operator instead of the built-in Grafana
   AlertManager which is not used.

   ![AlertManager list](static/monitoring-alertmanger-list.png)

   !!! warning

   It's important that you select the AlertManager that is managed by the
   Prometheus operator, otherwise your silence will not be applied to the
   Prometheus instance that is deployed as part of Atmosphere.

3. Click the "Add Silence" button and use the AlertManager format to create
   your silence, which you can test by seeing if it matches any alerts in the
   list labeled "Affected alert instances".

!!! note

    It is strongly recommended that you create a silence with the least amount
    of needed labels which will make sure that small minor changes to the
    alerts will not break your silence.

## Persistence

For Grafana, rather than enabling persistence through the application's user
interface or manual Helm chart modifications, dashboards should be managed
directly via the Helm chart values.

!!! warning

    It is important to avoid manual persistence configurations, especially for
    services like Grafana, where dashboards and data sources can be saved. Such
    practices are not captured in version control and pose a risk of data loss,
    configuration drift, and upgrade complications.

To manage Grafana dashboards through Helm, you can include the dashboard
definitions within your configuration file. By doing so, you facilitate
version-controlled dashboard configurations that can be replicated across
different deployments without manual intervention.

For example, a dashboard can be defined in the Helm values like this:

```yaml
kube_prometheus_stack_helm_values:
  grafana:
    dashboards:
      default:
        my-dashboard:
          gnetId: 10000
          revision: 1
          datasource: Prometheus
```

This instructs Helm to fetch and configure the specified dashboard from
[Grafana.com](https://grafana.com/grafana/dashboards/), using Prometheus as the data source.

You can find more examples of how to do this in the Grafana Helm chart
[Documentation](https://github.com/grafana/helm-charts/tree/main/charts/grafana#import-dashboards).
