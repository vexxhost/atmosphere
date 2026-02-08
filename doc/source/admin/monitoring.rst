#########################
Monitoring and operations
#########################

Atmosphere includes a Grafana deployment with dashboards created by default and
a Prometheus deployment that collects metrics from the cluster and sends alerts
to AlertManager. Loki also collects logs from the cluster using Vector.

******************************
Philosophy and alerting levels
******************************

Atmosphere's monitoring philosophy is strongly aligned with the principles
outlined in the `Google Site Reliability Engineering (SRE) book <https://sre.google/sre-book/>`_.
The approach focuses on alerting that's meaningful, practical, and directly
tied to user-visible impact.

Alerting philosophy
===================

Symptom-based alerting
----------------------

Symptom-based alerts take priority over cause-based alerts. They focus on
conditions that directly affect users or service health, such as elevated error
rates or increased latency, rather than internal system state.

Cause-based alerts are acceptable only when no reasonable symptom-based proxy
exists, or when they serve as leading indicators for capacity planning
(typically P4 or P5).

Error budget driven alerting
----------------------------

When service-level objectives (SLOs) exist for a service, burn-rate alerts
work better than static threshold alerts. A burn-rate alert fires when the
error budget depletes faster than expected, which accounts for baseline error
rates and avoids alerting on acceptable levels of degradation.

Escalation model
-----------------

The alerting system scales severity with impact. Most alerts affecting a single
system trigger a lower priority level (P4 or P5). If an issue affects the
entire control plane of a specific service, it escalates to a P3 or P2. If a
service is entirely unavailable, it becomes a P1.

Inhibition and grouping
-----------------------

Alerts have dependency awareness. When a parent component fails (for example, a
node goes down), inhibition rules in AlertManager suppress child component
alerts (for example, pods on that node) to avoid cascading alert storms.
The system groups related alerts so that a single notification represents a
coherent incident rather than dozens of individual symptoms.

Minimizing noise
-----------------

Minimizing alert noise keeps every notification meaningful and worthy of
action. Every alert should provide enough information to initiate an immediate
and effective response, regardless of business hours for high priority alerts.

Monitoring and alerting strategies improve over time to better identify and
respond to incidents. The ultimate goal is to provide a reliable and
high-quality service to all users.

Severity levels
===============

The alerting system classifies incidents into different severity levels based on
their impact on the system and users.

**P1**: Critical
  This level covers incidents causing a complete service disruption or
  significant loss of functionality across the entire Atmosphere platform.
  Immediate response, attention, and action are necessary regardless of
  business hours.

  Notification: Page to on-call engineer with escalation.

**P2**: High
  This level is for incidents that affect a large group of users or critical
  system components. These incidents require swift attention and action,
  regardless of business hours, but don't cause a total disruption.

  Notification: Page to on-call engineer.

**P3**: Moderate
  This level is for incidents that affect a smaller group of users or a single
  system. These incidents require attention and may necessitate action during
  business hours.

  Notification: Alert channel with mention.

**P4**: Low
  This level covers minor issues that have a limited impact on a small
  subset of users or system functionality. These incidents require attention
  and action, if necessary, during standard business hours.

  Notification: Alert channel, no mention.

**P5**: Informational
  This is the lowest level of severity, used for providing information about
  normal system activities or minor issues that don't significantly impact
  users or system functionality. These incidents typically don't require
  immediate attention or action and operators address them during standard
  business hours.

  Notification: Informational channel or email digest.

**********************
Operational procedures
**********************

Creating silences
=================

To create a silence, log in to your Grafana instance that Atmosphere deploys
as an admin user.

1. Click on the hamburger menu in the top left corner and select "Alerting"
   and then "Silences" from the menu.

   .. image:: images/monitoring-silences-menu.png
      :alt: Silences menu
      :width: 200

2. Make sure that you select "AlertManager" on the top right corner of the page,
   this ensures that you create a silence inside of the AlertManager
   that's managed by the Prometheus operator instead of the built-in Grafana
   AlertManager which isn't used.

    .. image:: images/monitoring-alertmanger-list.png
        :alt: AlertManager list
        :width: 200

   .. admonition:: AlertManager selection
    :class: warning

    It's important that you select the AlertManager that's managed by the
    Prometheus operator, otherwise your silence won't apply to the
    Prometheus instance that Atmosphere deploys.

3. Click the "Add Silence" button and use the AlertManager format to create
   your silence, which you can test by seeing if it matches any alerts in the
   list labeled "Affected alert instances".

.. admonition:: Limit the number of labels
    :class: info

    It's important to limit the number of labels that you use in your silence
    to make sure it continues to work even if the alerts change.

    For example, if you have an alert that carries the following labels:

    - ``alertname``
    - ``instance``
    - ``job``
    - ``severity``

    You should only use the ``alertname`` and ``severity`` labels in your
    silence to make sure it continues to work even if the ``instance``
    or ``job`` labels change.

**************
Configurations
**************

Dashboard management
====================

For Grafana, rather than enabling persistence through the application's user
interface or manual Helm chart modifications, manage dashboards directly via the
Helm chart values.

.. admonition:: Avoid Manual Persistence Configurations!
    :class: warning

    It's important to avoid manual persistence configurations, especially for
    services like Grafana, where dashboards and data sources can persist. Such
    practices aren't captured in version control and pose a risk of data loss,
    configuration drift, and upgrade complications.

To manage Grafana dashboards through Helm, include the dashboard definitions
within your configuration file. This approach enables version-controlled
dashboard configurations that you can replicate across different deployments
without manual intervention.

For example, you can define a dashboard in the Helm values like this:

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
Prometheus as the data source. You can find more examples of how to do
this in the Grafana Helm chart `Import Dashboards <https://github.com/grafana/helm-charts/tree/main/charts/grafana#import-dashboards>`_
documentation.

************
Viewing data
************

The monitoring stack offers a few different ways to view collected data. The most
common ways are through AlertManager, Grafana, and Prometheus.

Grafana dashboard
=================

By default, Atmosphere creates an ``Ingress`` for Grafana using the
``kube_prometheus_stack_grafana_host`` variable. Keycloak handles
authentication, and Atmosphere deploys it by default.

Inside Keycloak, Atmosphere creates two client roles for Grafana:

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

By default, Prometheus sits behind an ``Ingress`` using the
``kube_prometheus_stack_prometheus_host`` variable. It also runs behind the
`oauth2-proxy` service, which handles authentication so that only authenticated
users can access the Prometheus UI.

Alternative authentication
--------------------------

You can bypass the `oauth2-proxy` service and use an alternative authentication
method to access the Prometheus UI. In both cases, you override the
``servicePort`` on the ``Ingress`` to point to the port where Prometheus runs
instead of the `oauth2-proxy` service.

.. admonition:: Advanced Usage Only
    :class: warning

    It's strongly recommended that you stick to keeping the `oauth2-proxy`
    service in front of the Prometheus UI.  The `oauth2-proxy` service is
    responsible for authenticating users and ensuring that only authenticated
    users can access the Prometheus UI.

Basic authentication
~~~~~~~~~~~~~~~~~~~~

To use basic authentication for the Prometheus UI instead of the `oauth2-proxy`
service with single sign-on, make the following changes to your inventory:

.. code-block:: yaml

  kube_prometheus_stack_helm_values:
    prometheus:
      ingress:
        servicePort: 8080
        annotations:
          nginx.ingress.kubernetes.io/auth-type: basic
          nginx.ingress.kubernetes.io/auth-secret: basic-auth-secret-name

In this example, the ``basic-auth-secret-name`` secret handles user
authentication. Create the secret in the same namespace as the Prometheus
deployment based on the `Ingress NGINX annotations <https://github.com/kubernetes/ingress-nginx/blob/main/docs/user-guide/nginx-configuration/annotations.md#annotations>`_.

Restricting by address
~~~~~~~~~~~~~~~~~~~~~

To restrict Prometheus UI access to specific IP addresses, make the following
changes to your inventory:

.. code-block:: yaml

  kube_prometheus_stack_helm_values:
    prometheus:
      ingress:
        servicePort: 8080
        annotations:
          nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/24,172.10.0.1"

In this example, the configuration restricts access to the IP range
``10.0.0.0/24`` and the IP address ``172.10.0.1``.

AlertManager
============

By default, the AlertManager dashboard points to the Ansible variable
``kube_prometheus_stack_alertmanager_host`` and sits behind an ``Ingress``
with the `oauth2-proxy` service, protected by Keycloak similar to Prometheus.

************
Integrations
************

Since Atmosphere relies on AlertManager to send alerts, you can integrate it
with services like OpsGenie, PagerDuty, email, and more. To receive monitoring
alerts using your preferred notification tools, integrate them with
AlertManager.

OpsGenie
========

To get started, complete the following steps inside OpsGenie:

1. Create an integration inside OpsGenie, you can do this by going to
   *Settings* > *Integrations* > *Add Integration* and selecting *Prometheus*.
2. Copy the API key that OpsGenie generates for you and set up correct
   assignment rules inside OpsGenie.
3. Create a new heartbeat inside OpsGenie, you can do this by going to
   *Settings* > *Heartbeats* > *Create Heartbeat*. Set the interval to 1 minute.

Afterward, configure the following options for the Atmosphere ``config``,
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

Once you deploy the changes, you'll start to see alerts inside OpsGenie and
you can also verify that the heartbeat shows as *ACTIVE*.

PagerDuty
=========

To integrate with PagerDuty, first prepare an *Integration key*. To do that,
decide how you want to integrate with PagerDuty since there are two ways:

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
``pagerduty_configs`` in the `Prometheus documentation <https://prometheus.io/docs/alerting/latest/configuration/#pagerduty_config>`_.

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
``email_configs`` in the `Prometheus documentation <https://prometheus.io/docs/alerting/latest/configuration/#email_configs>`_.

****************
Alerts reference
****************

``etcdDatabaseHighFragmentationRatio``
======================================

This alert fires when the etcd database has a high fragmentation ratio that can
cause performance issues on the cluster. To resolve this issue, use the
following command:

.. code-block:: console

  kubectl -n kube-system exec svc/kube-prometheus-stack-kube-etcd -- \
    etcdctl defrag \
    --cluster \
    --cacert /etc/kubernetes/pki/etcd/ca.crt \
    --key /etc/kubernetes/pki/etcd/server.key \
    --cert /etc/kubernetes/pki/etcd/server.crt

``EtcdMembersDown``
===================

If any alerts fire from Prometheus for ``etcd`` issues such as ``TargetDown``,
``etcdMembersDown``, or ``etcdInsufficientMembers``, it could be due to expired
certificates. You can update the certificates that ``kube-prometheus-stack`` uses for
talking with ``etcd`` with the following commands:

.. code-block:: console

  kubectl -n monitoring delete secret/kube-prometheus-stack-etcd-client-cert
  kubectl -n monitoring create secret generic kube-prometheus-stack-etcd-client-cert \
      --from-file=/etc/kubernetes/pki/etcd/ca.crt \
      --from-file=/etc/kubernetes/pki/etcd/healthcheck-client.crt \
      --from-file=/etc/kubernetes/pki/etcd/healthcheck-client.key

``GoldpingerHighErrorRate``
===========================

This alert fires when more than 5% of Goldpinger ping attempts are failing for
at least 15 minutes, indicating network connectivity issues across the cluster.

**Likely Root Causes**

- Intermittent network connectivity issues
- DNS resolution failures
- Firewall rules blocking ICMP or health check traffic
- Goldpinger pods experiencing resource constraints
- Node-level network stack issues

**Diagnostic and Remediation Steps**

1. Check error rates by node to identify patterns:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (instance) (rate(goldpinger_errors_total{type="ping"}[5m]))'

2. Verify Goldpinger pods are healthy:

   .. code-block:: console

     kubectl -n monitoring get pods -l app.kubernetes.io/name=goldpinger
     kubectl -n monitoring describe pods -l app.kubernetes.io/name=goldpinger

3. Check for any network policies that might be blocking traffic:

   .. code-block:: console

     kubectl get networkpolicies --all-namespaces

4. Review Goldpinger logs for specific error messages:

   .. code-block:: console

     kubectl -n monitoring logs -l app.kubernetes.io/name=goldpinger --tail=100

5. Check if the errors correlate with specific target nodes by examining
   which targets have high latency:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'topk(10, histogram_quantile(0.95, sum by (instance, host_ip, le) (rate(goldpinger_peers_response_time_s_bucket{call_type="ping"}[5m]))))'

``GoldpingerHighPeerLatency``
=============================

This alert fires when the 95th percentile of Goldpinger peer-to-peer latency
exceeds 500ms for at least 15 minutes, indicating network congestion or
performance issues.

**Likely Root Causes**

- Network congestion on the cluster network
- Overloaded network switches or routers
- High CPU or I/O load on nodes causing delayed responses
- Network interface saturation
- Incorrect network Quality of Service (QoS) configuration

**Diagnostic and Remediation Steps**

1. Check which node pairs have the highest latency:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'topk(10, histogram_quantile(0.95, sum by (instance, host_ip, le) (rate(goldpinger_peers_response_time_s_bucket{call_type="ping"}[5m]))))'

2. Check node-exporter metrics for network saturation:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'rate(node_network_transmit_bytes_total[5m])'

3. Review CPU and I/O wait metrics on affected nodes:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (instance) (rate(node_cpu_seconds_total{mode="iowait"}[5m]))'

4. Check for network drops which may indicate congestion:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'rate(node_network_receive_drop_total[5m]) > 0'

5. If latency is consistently high between specific node pairs, investigate
   the network path between them for hardware issues or configuration errors.

``GoldpingerHighUnhealthyRatio``
================================

This alert fires when more than 10% of nodes in the cluster are reporting as
unhealthy according to Goldpinger health checks for at least 5 minutes.

**Likely Root Causes**

- Widespread network connectivity issues affecting multiple nodes
- A network partition isolating a segment of the cluster
- Multiple nodes experiencing high load or resource exhaustion
- Infrastructure-level network problems (switch failures, routing issues)

**Diagnostic and Remediation Steps**

1. Check the Goldpinger dashboard in Grafana to visualize which nodes are
   affected and the connectivity patterns.

2. Query Prometheus to identify which specific nodes are reporting unhealthy:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'goldpinger_nodes_health_total{status="unhealthy"} > 0'

3. Check for network issues on the affected nodes:

   .. code-block:: console

     kubectl get nodes -o wide
     kubectl describe node <affected-node>

4. Review node-exporter metrics for network errors or drops:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'rate(node_network_receive_errs_total[5m]) > 0'

5. If the issue affects only specific nodes, check their network
   configuration and physical connectivity.

``GoldpingerNodeUnreachable``
=============================

This alert fires when more than 50% of Goldpinger instances can't reach a
specific node for at least 5 minutes. The target node may be down or
experiencing network issues.

**Likely Root Causes**

- The target node is down or unresponsive
- Network interface failure on the target node
- Firewall or security group configuration error blocking traffic
- The Goldpinger pod on the target node has crashed

**Diagnostic and Remediation Steps**

1. Identify the affected node by its IP address from the alert labels:

   .. code-block:: console

     kubectl get nodes -o wide | grep <host_ip>

2. Check if the node is reachable and healthy:

   .. code-block:: console

     kubectl get node <node-name>
     kubectl describe node <node-name>

3. Verify the Goldpinger pod is running on the affected node:

   .. code-block:: console

     kubectl -n monitoring get pods -l app.kubernetes.io/name=goldpinger \
       -o wide | grep <node-name>

4. Check network connectivity from another node:

   .. code-block:: console

     kubectl debug node/<healthy-node> -it --image=busybox -- \
       ping -c 3 <affected-node-ip>

5. Review system logs on the affected node for network or kernel issues:

   .. code-block:: console

     kubectl debug node/<affected-node> -it --image=busybox -- \
       cat /host/var/log/syslog | tail -100

``NginxIngressCriticalErrorRate``
=================================

This alert fires when a service behind NGINX Ingress is returning 5xx errors at
a rate exceeding 20% for at least 5 minutes, indicating severe service
degradation that requires immediate attention.

**Likely Root Causes**

- Backend service pods are crashing or in a crash loop
- Database connection failures affecting all service replicas
- Configuration errors in the service deployment
- Resource exhaustion (CPU, memory, or file descriptors) on backend pods
- Network issues between NGINX and backend services
- Backend service code bugs causing widespread failures

**Diagnostic and Remediation Steps**

1. Identify which specific service is affected from the alert labels and check
   the current error rate:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[5m])) / sum by (service) (rate(nginx_ingress_controller_requests[5m]))'

2. Check the health and status of the backend service pods:

   .. code-block:: console

     kubectl get pods -A | grep <service-name>
     kubectl describe pod <pod-name> -n <namespace>

3. Review recent logs from the affected service pods:

   .. code-block:: console

     kubectl logs -n <namespace> <pod-name> --tail=100

4. Check NGINX Ingress controller logs for upstream connection errors:

   .. code-block:: console

     kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=200

5. Verify resource usage on the backend service pods:

   .. code-block:: console

     kubectl top pods -n <namespace> | grep <service-name>

6. If the issue persists, consider scaling the service or restarting affected
   pods to attempt recovery while investigating the root cause.

``NginxIngressHighErrorRate``
=============================

This alert fires when a service behind NGINX Ingress is returning 5xx errors at
a rate exceeding 5% for at least 15 minutes. This indicates elevated error
rates that may be affecting user experience but haven't reached critical levels.

**Likely Root Causes**

- Intermittent issues with a subset of backend service replicas
- Occasional database query timeouts or connection pool exhaustion
- Resource pressure on some backend pods
- Networking issues affecting specific nodes or pods
- Recent deployment causing partial service degradation
- Cache or session storage issues

**Diagnostic and Remediation Steps**

1. Check the current error rate by service:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[5m])) / sum by (service) (rate(nginx_ingress_controller_requests[5m]))'

2. Identify which specific HTTP error codes are being returned:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service, status) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[5m]))'

3. Check for unhealthy or recently restarted pods:

   .. code-block:: console

     kubectl get pods -A | grep <service-name>
     kubectl get events -n <namespace> --sort-by='.lastTimestamp' | grep <service-name>

4. Review application logs for errors:

   .. code-block:: console

     kubectl logs -n <namespace> -l app=<service-name> --tail=100 | grep -i error

5. Check if the error rate correlates with increased load or specific API
   endpoints by examining the NGINX Ingress metrics in Grafana.

6. Verify database connectivity and performance if the service depends on a
   database:

   .. code-block:: console

     kubectl exec -it <pod-name> -n <namespace> -- <database-client> -e "SHOW PROCESSLIST;"

``NodeNetworkMulticast``
========================

This alert fires when a node receives large volumes of multicast traffic, which
can indicate an incorrectly configured network or a malicious actor.

This can result in high CPU usage on the node and can cause the node to become
unresponsive. It can also cause a high amount of software interrupts on the
node.

To find the root cause of this issue, use the following commands:

.. code-block:: console

  iftop -ni $DEV -f 'multicast and not broadcast'

With this command, you can see which IP addresses send the multicast traffic.
Once you have the IP address, use the following command to find the server
behind it:

.. code-block:: console

  openstack server list --all-projects --long -n --ip $IP
