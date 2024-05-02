#########################
Monitoring and Operations
#########################

There is a Grafana deployment with a few dashboards that are created by default
and a Prometheus deployment that is used to collect metrics from the cluster
which sends alerts to AlertManager. In addition, Loki is deployed to collect
logs from the cluster using Vector.

******************************
Philosophy and Alerting Levels
******************************

Atmosphere's monitoring philosophy is strongly aligned with the principles
outlined in the Google Site Reliability Engineering (SRE) book. Our approach
focuses on alerting on conditions that are symptomatic of issues which directly
impact the service or system health, rather than simply monitoring the state of
individual components.

Alerting Philosophy
===================

Our alerting philosophy aims to alert the right people at the right time. Most
alerts, if they are affecting a single system, would trigger a lower priority
level (P4 or P5). However, if an issue is affecting the entire control plane of
a specific service, it might escalate to a P3 or P2. And if the whole service
is unavailable, it becomes a P1.

We believe in minimizing alert noise to ensure that alerts are meaningful and
actionable. Our goal is to have every alert provide enough information to
initiate an immediate and effective response, regardless of business hours for
high priority alerts.

We continue to refine our monitoring and alerting strategies to ensure that we
are effectively identifying and responding to incidents. The ultimate goal is
to provide a reliable and high-quality service to all our users.

Severity Levels
===============

Our alerting system classifies incidents into different severity levels based on
their impact on the system and users.

**P1**: Critical
  This level is used for incidents causing a complete service disruption or
  significant loss of functionality across the entire Atmosphere platform.
  Immediate response, attention, and action are necessary regardless of
  business hours.

**P2**: High
  This level is for incidents that affect a large group of users or critical
  system components. These incidents require swift attention and action,
  regardless of business hours, but do not cause a total disruption.

**P3**: Moderate
  This level is for incidents that affect a smaller group of users or a single
  system. These incidents require attention and may necessitate action during
  business hours.

**P4**: Low
  This level is used for minor issues that have a limited impact on a small
  subset of users or system functionality. These incidents require attention
  and action, if necessary, during standard business hours.

**P5**: Informational
  This is the lowest level of severity, used for providing information about
  normal system activities or minor issues that don't significantly impact
  users or system functionality. These incidents typically do not require
  immediate attention or action and are addressed during standard business
  hours.

**********************
Operational Procedures
**********************

Creating silences
=================

In order to create a silence, you'll need to login to your Grafana instance that
is deployed as part of Atmosphere as an admin user.

1. Click on the hamburger menu in the top left corner and select "Alerting"
   and then "Silences" from the menu.

   .. image:: images/monitoring-silences-menu.png
      :alt: Silences menu
      :width: 200

2. Ensure that you select "AlertManager" on the top right corner of the page,
   this will make sure that you create a silence inside of the AlertManager
   that is managed by the Prometheus operator instead of the built-in Grafana
   AlertManager which is not used.

    .. image:: images/monitoring-alertmanger-list.png
        :alt: AlertManager list
        :width: 200

   .. admonition:: AlertManager selection
    :class: warning

    It's important that you select the AlertManager that is managed by the
    Prometheus operator, otherwise your silence will not be applied to the
    Prometheus instance that is deployed as part of Atmosphere.

3. Click the "Add Silence" button and use the AlertManager format to create
   your silence, which you can test by seeing if it matches any alerts in the
   list labeled "Affected alert instances".

.. admonition:: Limit the number of labels
    :class: info

    It is important to limit the number of labels that you use in your silence
    to ensure that it will continue to work even if the alerts are modified.

    For example, if you have an alert that is labeled with the following labels:

    - ``alertname``
    - ``instance``
    - ``job``
    - ``severity``

    You should only use the ``alertname`` and ``severity`` labels in your
    silence to ensure that it will continue to work even if the ``instance``
    or ``job`` labels are modified.

**************
Configurations
**************

Dashboard Management
====================

For Grafana, rather than enabling persistence through the application's user
interface or manual Helm chart modifications, dashboards should be managed
directly via the Helm chart values.

.. admonition:: Avoid Manual Persistence Configurations!
    :class: warning

    It is important to avoid manual persistence configurations, especially for
    services like Grafana, where dashboards and data sources can be saved. Such
    practices are not captured in version control and pose a risk of data loss,
    configuration drift, and upgrade complications.

To manage Grafana dashboards through Helm, you can include the dashboard
definitions within your configuration file. By doing so, you facilitate
version-controlled dashboard configurations that can be replicated across
different deployments without manual intervention.

For example, a dashboard can be defined in the Helm values like this:

.. code-block:: yaml

  kube_prometheus_stack_helm_values:
    grafana:
      dashboards:
        default:
          my-dashboard:
            gnetId: 10000
            revision: 1
            datasource: Prometheus

This instructs Helm to fetch and configure the specified dashboard from
`Grafana.com dashboards <https://grafana.com/grafana/dashboards/>`_, using
Prometheus as the data source.  You can find more examples of how to do
this in the Grafana Helm chart `Import Dashboards <https://github.com/grafana/helm-charts/tree/main/charts/grafana#import-dashboards>`_
documentation.

************
Viewing data
************

There are a few different ways to view the data that is collected by the
monitoring stack.  The most common ways are through AlertManager, Grafana, and
Prometheus.

Grafana dashboard
=================

By default, an ``Ingress`` is created for Grafana using the
``kube_prometheus_stack_grafana_host`` variable.  The authentication is done
using the Keycloak service which is deployed by default.

Inside Keycloak, there are two client roles that are created for Grafana:

``grafana:admin``
  Has access to all organization resources, including dashboards, users, and
  teams.

``grafana:editor``
  Can view and edit dashboards, folders, and playlists.

``grafana:viewer``
  Can view dashboards, playlists, and query data sources.

You can view the existing dashboards by going to *Manage* > *Dashboards*. You
can also check any alerts that are currently firing by going to *Alerting* >
*Alerts*.

Prometheus
==========

By default, Prometheus is exposed behind an ``Ingress`` using the
``kube_prometheus_stack_prometheus_host`` variable.  In addition, it is also
running behind the `oauth2-proxy` service which is used for authentication
so that only authenticated users can access the Prometheus UI.

Alternative Authentication
--------------------------

It is possible to by-pass the `oauth2-proxy` service and use an alternative
authentication method to access the Prometheus UI.  In both cases, we will
be overriding the ``servicePort`` on the ``Ingress`` to point to the port
where Prometheus is running and not the `oauth2-proxy` service.

.. admonition:: Advanced Usage Only
    :class: warning

    It's strongly recommended that you stick to keeping the `oauth2-proxy`
    service in front of the Prometheus UI.  The `oauth2-proxy` service is
    responsible for authenticating users and ensuring that only authenticated
    users can access the Prometheus UI.

Basic Authentication
~~~~~~~~~~~~~~~~~~~~

If you want to rely on basic authentication to access the Prometheus UI instead
of using the `oauth2-proxy` service to expose it over single sign-on, you can
do so by making the following changes to your inventory:

.. code-block:: yaml

  kube_prometheus_stack_helm_values:
    prometheus:
      ingress:
        servicePort: 8080
        annotations:
          nginx.ingress.kubernetes.io/auth-type: basic
          nginx.ingress.kubernetes.io/auth-secret: basic-auth-secret-name

In the example above, we are using the ``basic-auth-secret-name`` secret to
authenticate users.  The secret should be created in the same namespace as the
Prometheus deployment based on the `Ingress NGINX Annotations <https://github.com/kubernetes/ingress-nginx/blob/main/docs/user-guide/nginx-configuration/annotations.md#annotations>`_.

IP Whitelisting
~~~~~~~~~~~~~~~

If you want to whitelist specific IPs to access the Prometheus UI, you can do
so by making the following changes to your inventory:

.. code-block:: yaml

  kube_prometheus_stack_helm_values:
    prometheus:
      ingress:
        servicePort: 8080
        annotations:
          nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/24,172.10.0.1"

In the example above, we are whitelisting the IP range ``10.0.0.0/24`` and the IP address
``172.10.0.1``.

AlertManager
============

By default, the AlertManager dashboard is pointing to the Ansible variable
``kube_prometheus_stack_alertmanager_host`` and is exposed using an ``Ingress``
behind the `oauth2-proxy` service, protected by Keycloak similar to Prometheus.

************
Integrations
************

Since Atmosphere relies on AlertManager to send alerts, it is possible to
integrate it with services like OpsGenie, PagerDuty, email and more.  To
receive monitoring alerts using your preferred notification tools, you'll
need to integrate them with AlertManager.

OpsGenie
========

In order to get started, you will need to complete the following steps inside
OpsGenie:

1. Create an integration inside OpsGenie, you can do this by going to
   *Settings* > *Integrations* > *Add Integration* and selecting *Prometheus*.
2. Copy the API key that is generated for you and setup correct assignment
   rules inside OpsGenie.
3. Create a new heartbeat inside OpsGenie, you can do this by going to
   *Settings* > *Heartbeats* > *Create Heartbeat*. Set the interval to 1 minute.

Afterwards, you can configure the following options for the Atmosphere config,
making sure that you replace the placeholders with the correct values:

``API_KEY``
  The API key that you copied from the OpsGenie integration.

``HEARTBEAT_NAME``
  The name of the heartbeat that you created inside OpsGenie

.. code-block:: yaml

  kube_prometheus_stack_helm_values:
    alertmanager:
      config:
        receivers:
          - name: "null"
          - name: notifier
            opsgenie_configs:
              - api_key: API_KEY
                message: >-
                  {% raw -%}
                  {{ .GroupLabels.alertname }}
                  {%- endraw %}
                priority: >-
                  {% raw -%}
                  {{- if eq .GroupLabels.severity "critical" -}}
                  P1
                  {{- else if eq .GroupLabels.severity "warning" -}}
                  P3
                  {{- else if eq .GroupLabels.severity "info" -}}
                  P5
                  {{- else -}}
                  {{ .GroupLabels.severity }}
                  {{- end -}}
                  {%- endraw %}
                description: |-
                  {% raw -%}
                  {{ if gt (len .Alerts.Firing) 0 -}}
                  Alerts Firing:
                  {{ range .Alerts.Firing }}
                    - Message: {{ .Annotations.message }}
                      Labels:
                  {{ range .Labels.SortedPairs }}   - {{ .Name }} = {{ .Value }}
                  {{ end }}   Annotations:
                  {{ range .Annotations.SortedPairs }}   - {{ .Name }} = {{ .Value }}
                  {{ end }}   Source: {{ .GeneratorURL }}
                  {{ end }}
                  {{- end }}
                  {{ if gt (len .Alerts.Resolved) 0 -}}
                  Alerts Resolved:
                  {{ range .Alerts.Resolved }}
                    - Message: {{ .Annotations.message }}
                      Labels:
                  {{ range .Labels.SortedPairs }}   - {{ .Name }} = {{ .Value }}
                  {{ end }}   Annotations:
                  {{ range .Annotations.SortedPairs }}   - {{ .Name }} = {{ .Value }}
                  {{ end }}   Source: {{ .GeneratorURL }}
                  {{ end }}
                  {{- end }}
                  {%- endraw %}
          - name: heartbeat
            webhook_configs:
              - url: https://api.opsgenie.com/v2/heartbeats/HEARTBEAT_NAME/ping
                send_resolved: false
                http_config:
                  basic_auth:
                    password: API_KEY

Once this is done and deployed, you'll start to see alerts inside OpsGenie and
you can also verify that the heartbeat is listed as *ACTIVE*.

PagerDuty
=========

To integrate with Pagerduty, first you need to prepare an *Integration key*. In
order to do that, you must decide how you want to integrate with PagerDuty since
there are two ways to do it:

**Event Orchestration**
  This method is beneficial if you want to build different routing rules based
  on the events coming from the integrated tool.

**PagerDuty Service Integration**
  This method is beneficial if you don't need to route alerts from the integrated
  tool to different responders based on the event payload.

For both of these methods, you need to create an *Integration key* in PagerDuty
using the `PagerDuty Integration Guide <https://www.pagerduty.com/docs/guides/prometheus-integration-guide/>`_.

Once you're done, you'll need to configure the inventory with the following
options:

.. code-block:: yaml

  kube_prometheus_stack_helm_values:
    alertmanager:
      config:
        receivers:
          - name: notifier
            pagerduty_configs:
              - service_key: '<your integration key here>'

You can find more details about
`pagerduty_configs <https://prometheus.io/docs/alerting/latest/configuration/#pagerduty_config>`_
in the Prometheus documentation.

Email
=====

To integrate with email, you need to configure the following options in the
inventory:

.. code-block:: yaml

  kube_prometheus_stack_helm_values:
    alertmanager:
      config:
        receivers:
          - name: notifier
            email_configs:
              - smarthost: 'smtp.gmail.com:587'
                auth_username: '<your email id here>'
                auth_password: '<your email password here>'
                from: '<your email id here>'
                to: '<receiver's email id here>'
                headers:
                  subject: 'Prometheus Mail Alerts'

You can find more details about
`email_configs <https://prometheus.io/docs/alerting/latest/configuration/#email_configs>`_
in the Prometheus documentation.

****************
Alerts Reference
****************

``etcdDatabaseHighFragmentationRatio``
  This alert is triggered when the etcd database has a high fragmentation ratio
  which can cause performance issues on the cluster.  In order to resolve this
  issue, you can use the following command:

  .. code-block:: console

    kubectl -n kube-system exec svc/kube-prometheus-stack-kube-etcd -- \
      etcdctl defrag \
      --cluster \
      --cacert /etc/kubernetes/pki/etcd/ca.crt \
      --key /etc/kubernetes/pki/etcd/server.key \
      --cert /etc/kubernetes/pki/etcd/server.crt

``NodeNetworkMulticast``
  This alert is triggered when a node is receiving large volumes of multicast
  traffic which can be a sign of a misconfigured network or a malicious actor.

  This can result in high CPU usage on the node and can cause the node to become
  unresponsive. Also, it can be the cause of a very high amount of software
  interrupts on the node.

  In order to find the root cause of this issue, you can use the following
  commands:

  .. code-block:: console

    iftop -ni $DEV -f 'multicast and not broadcast'

  With the command above, you're able to see which IP addresses are sending the
  multicast traffic. Once you have the IP address, you can use the following
  command to find the server behind it:

  .. code-block:: console

    openstack server list --all-projects --long -n --ip $IP
