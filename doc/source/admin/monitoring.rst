#########################
Monitoring and operations
#########################

Atmosphere includes a Grafana deployment with dashboards created by default and
a Prometheus deployment that collects metrics from the cluster and sends alerts
to Alertmanager. Loki also collects logs from the cluster using Vector.
The default dashboards include an OpenStack deployment capacity view that uses
Placement metrics to show schedulable vCPU, RAM, and disk capacity.

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
node goes down), inhibition rules in Alertmanager suppress child component
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

2. Make sure that you select "Alertmanager" on the top right corner of the page,
   this ensures that you create a silence inside of the Alertmanager
   that's managed by the Prometheus operator instead of the built-in Grafana
   Alertmanager which isn't used.

    .. image:: images/monitoring-alertmanger-list.png
        :alt: Alertmanager list
        :width: 200

   .. admonition:: Alertmanager selection
    :class: warning

    It's important that you select the Alertmanager that's managed by the
    Prometheus operator, otherwise your silence won't apply to the
    Prometheus instance that Atmosphere deploys.

3. Click the "Add Silence" button and use the Alertmanager format to create
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

Atmosphere also ships default Grafana dashboard ``ConfigMap`` objects from the
``kube_prometheus_stack`` role. These dashboards are loaded by Grafana's
dashboard sidecar when the monitoring stack is deployed.

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
common ways are through Alertmanager, Grafana, and Prometheus.

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

Alertmanager
============

By default, the Alertmanager dashboard points to the Ansible variable
``kube_prometheus_stack_alertmanager_host`` and sits behind an ``Ingress``
with the `oauth2-proxy` service, protected by Keycloak similar to Prometheus.

************
Integrations
************

Since Atmosphere relies on Alertmanager to send alerts, you can integrate it
with services like OpsGenie, PagerDuty, email, and more. To receive monitoring
alerts using your preferred notification tools, integrate them with
Alertmanager.

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

``CoreDNSCriticalErrorBudgetBurn``
==================================

This alert fires when the CoreDNS SERVFAIL rate exceeds 14.4x the
burn rate for a 99.9% SLO. At this rate, the 30-day error budget
exhausts in under 2.1 days. It uses multi-window burn-rate detection
with 1-hour and 5-minute windows.

**Likely root causes**

- Upstream DNS servers are unreachable or returning errors
- CoreDNS configuration errors after a recent change
- Network connectivity issues between CoreDNS and upstream resolvers
- Resource exhaustion (CPU or memory) on CoreDNS pods

**Diagnostic and remediation steps**

1. Check CoreDNS pod health and logs:

   .. code-block:: console

     kubectl -n kube-system get pods -l k8s-app=kube-dns
     kubectl -n kube-system logs -l k8s-app=kube-dns --tail=100

2. Verify upstream DNS server connectivity:

   .. code-block:: console

     kubectl -n kube-system exec -it deploy/coredns -- nslookup example.com

3. Check the current SERVFAIL rate:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum(rate(coredns_dns_responses_total{rcode="SERVFAIL"}[5m])) / sum(rate(coredns_dns_responses_total[5m]))'

4. Review CoreDNS ConfigMap for configuration issues:

   .. code-block:: console

     kubectl -n kube-system get configmap coredns -o yaml

5. Restart CoreDNS pods if configuration looks correct:

   .. code-block:: console

     kubectl -n kube-system rollout restart deployment coredns

``CoreDNSDown``
===============

This alert fires when CoreDNS disappears from Prometheus target discovery for
more than 15 minutes. This could indicate crashed pods or an incorrectly
configured scrape target.

**Likely root causes**

- CoreDNS pods crashed or aren't scheduling
- Prometheus scrape configuration changed
- Node-level issues preventing pod scheduling
- Resource limits causing out-of-memory termination

**Diagnostic and remediation steps**

1. Check CoreDNS pod status:

   .. code-block:: console

     kubectl -n kube-system get pods -l k8s-app=kube-dns
     kubectl -n kube-system describe pods -l k8s-app=kube-dns

2. Check for out-of-memory events:

   .. code-block:: console

     kubectl -n kube-system get events --field-selector reason=OOMKilling

3. Verify Prometheus can reach the CoreDNS metrics endpoint:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 'up{job="coredns"}'

4. Check node availability if pods aren't scheduling:

   .. code-block:: console

     kubectl get nodes -o wide

``CoreDNSHighErrorBudgetBurn``
==============================

This alert fires when the CoreDNS SERVFAIL rate exceeds 6x the burn rate
for a 99.9% SLO. At this rate, the 30-day error budget exhausts in under
5 days. It uses multi-window burn-rate detection with 6-hour and 30-minute
windows.

**Likely root causes**

- Intermittent upstream DNS server issues
- Partial network connectivity problems
- DNS zone transfer failures
- Upstream rate limiting

**Diagnostic and remediation steps**

1. Check CoreDNS logs for recurring errors:

   .. code-block:: console

     kubectl -n kube-system logs -l k8s-app=kube-dns --tail=200 | grep -i error

2. Check the SERVFAIL rate broken down over time:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum(rate(coredns_dns_responses_total{rcode="SERVFAIL"}[30m])) / sum(rate(coredns_dns_responses_total[30m]))'

3. Verify upstream DNS server health by testing resolution:

   .. code-block:: console

     kubectl -n kube-system exec -it deploy/coredns -- nslookup example.com

4. Review CoreDNS forward plugin configuration:

   .. code-block:: console

     kubectl -n kube-system get configmap coredns -o yaml

``CoreDNSLowErrorBudgetBurn``
=============================

This alert fires when the CoreDNS SERVFAIL rate exceeds 1x the burn rate
for a 99.9% SLO. At this rate, the error budget exhausts before the 30-day
window resets. It uses multi-window burn-rate detection with 3-day and 6-hour
windows.

**Likely root causes**

- Chronic low-level DNS resolution failures
- Specific zones or domains consistently failing
- Degraded upstream DNS server performance
- Incorrectly configured DNS records causing intermittent failures

**Diagnostic and remediation steps**

1. Identify which DNS queries are failing:

   .. code-block:: console

     kubectl -n kube-system logs -l k8s-app=kube-dns --tail=500 | grep SERVFAIL

2. Check the long-term SERVFAIL trend:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum(rate(coredns_dns_responses_total{rcode="SERVFAIL"}[6h])) / sum(rate(coredns_dns_responses_total[6h]))'

3. Review if specific upstream servers are consistently problematic:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (to) (rate(coredns_forward_responses_total{rcode="SERVFAIL"}[6h]))'

``CoreDNSModerateErrorBudgetBurn``
==================================

This alert fires when the CoreDNS SERVFAIL rate exceeds 3x the burn rate
for a 99.9% SLO. At this rate, the 30-day error budget exhausts in under
10 days. It uses multi-window burn-rate detection with 1-day and 2-hour
windows.

**Likely root causes**

- Degraded upstream DNS server responding with errors
- Network path issues causing intermittent resolution failures
- DNS zone configuration errors causing partial failures
- Resource pressure on CoreDNS pods

**Diagnostic and remediation steps**

1. Check CoreDNS resource usage:

   .. code-block:: console

     kubectl -n kube-system top pods -l k8s-app=kube-dns

2. Review the SERVFAIL rate trend over the last day:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum(rate(coredns_dns_responses_total{rcode="SERVFAIL"}[2h])) / sum(rate(coredns_dns_responses_total[2h]))'

3. Check forward plugin health:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum(rate(coredns_forward_healthcheck_failures_total[2h]))'

4. Review CoreDNS logs for patterns:

   .. code-block:: console

     kubectl -n kube-system logs -l k8s-app=kube-dns --tail=300 | grep -i "error\|fail"

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

``GeneveTransmitErrors``
========================

This alert fires when a ``node-exporter`` device meets both of these
conditions:

- The ``ethtool`` collector reports it as a ``Geneve`` interface.
- The ``netdev`` collector reports more than 1.67 transmit errors per second
  over a 5-minute window, sustained for 15 minutes.

That rate equates to about 100 errors per minute.

This is a symptom proxy for tenant overlay transmit failures on a compute host.
It's not specific to one root cause: the Linux ``Geneve`` transmit path
increments errors when encapsulation or underlay transmit fails.

**Likely Root Causes**

- Underlay bond or path ``MTU`` is too small for encapsulated ``Geneve``
  traffic.
- Route lookup or underlay connectivity failure for the tunnel destination.
- ``Geneve`` socket or ``Open vSwitch`` ``datapath`` problem on the affected
  host.
- ``NIC`` driver, firmware, or offload issue on the underlay link.

**Diagnostic and Remediation Steps**

1. Identify the affected node, ``Geneve`` device, and error rate:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       '(rate(node_network_transmit_errs_total[5m])
         * on(instance, device) group_left(driver)
         node_ethtool_info{driver="geneve"})'

2. On the node, inspect the ``Geneve`` interface reported by the alert:

   .. code-block:: console

     ip -d link show <geneve-device>

   For ``OVN``/``Open vSwitch``, the system ``Geneve`` device usually appears as
   ``genev_sys_<udp-port>`` and shows ``geneve external``. Other ``Geneve``
   interfaces, such as ``Cilium`` tunnel devices, may also match this alert
   because the selector intentionally uses the ``ethtool`` ``driver="geneve"``
   label rather than an interface-name convention.

3. Confirm the underlay ``MTU`` is large enough for the encapsulated traffic:

   .. code-block:: console

     ip -d link show bond0
     ip -d link show bond0.4092

   If the bond ``MTU`` is below the fleet-canonical value (typically 9216 on
   jumbo deployments), correct the ``netplan`` or interfaces configuration and
   reapply, then verify with ``ip -d link show bond0``.

4. Check for an existing ``MTU`` consistency alert, such as
   ``CephNodeInconsistentMTU``, and compare ``node_network_mtu_bytes`` across
   peers if multiple hosts show the same symptoms.

5. If ``MTU`` is correct, inspect ``Open vSwitch`` and the underlay device for
   ``datapath`` or offload failures:

   .. code-block:: console

     ovs-appctl dpctl/show -s
     ovs-vsctl show
     ethtool -S bond0

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

``IpmiUncorrectableMemoryError``
================================

This alert fires when the Intelligent Platform Management Interface (IPMI)
exporter reports a recent ``uncorrectable_memory_error`` System Event Log
(SEL) event. These events
indicate a non-recoverable memory error on the host and often require
hardware intervention.

**Likely Root Causes**

- Failing dual in-line memory module (DIMM) or memory controller
- Unstable firmware or Basic Input/Output System (BIOS) configuration
- Recent hardware changes or maintenance introducing faulty memory

**Diagnostic and Remediation Steps**

1. Identify the affected host from the alert ``instance`` label.

2. Check the SEL (System Event Log) on the host for uncorrectable memory errors:

   .. code-block:: console

     ipmitool sel list | grep -i "uncorrectable"

3. Review system logs for error-correcting code (ECC) or memory errors:

   .. code-block:: console

     journalctl -k | grep -i -e ecc -e memory -e edac

4. If the error recurs, replace the failing DIMM (dual in-line memory module)
   and run a memory test
   (for example, ``memtest86``) before returning the host to service.

``IpmiUnrecoverableCpuError``
=============================

This alert fires when the IPMI (Intelligent Platform Management Interface)
exporter reports a recent ``unrecoverable_cpu_error`` SEL (System Event Log)
event. These events
indicate a fatal CPU error that typically requires hardware
intervention and may precede a crash.

**Likely Root Causes**

- Failing CPU or socket
- Hardware instability due to power or thermal issues
- Firmware or microcode issues

**Diagnostic and Remediation Steps**

1. Identify the affected host from the alert ``instance`` label.

2. Check the SEL (System Event Log) on the host for CPU errors:

   .. code-block:: console

     ipmitool sel list | grep -i -e "processor" -e "err"

3. Review system logs for machine check or CPU errors:

   .. code-block:: console

     journalctl -k | grep -i -e mce -e machine -e cpu

4. Check CPU temperatures and system health:

   .. code-block:: console

     ipmitool sdr type temperature
     ipmitool sdr type processor

5. If the error recurs, schedule hardware maintenance and replace the
   affected CPU or motherboard as needed.

``MySQLGaleraOutOfSync``
========================

This alert fires when a Percona XtraDB Cluster (PXC) Galera node has a
``wsrep_local_state`` that's not 4 (Synced) and not 2 (Donor), while
``wsrep_desync`` isn't enabled. The alert excludes state 2 (Donor) because
it's a normal transient state during donor operations for State Snapshot
Transfer (SST) or PXC operator backups. The separate
``MySQLGaleraDonorFallingBehind`` alert covers problematic donor
scenarios.

This is a cause-based alert because no reasonable symptom-based proxy exists
for a Galera node losing cluster sync. The cluster may continue to serve
requests with the remaining nodes, but the reduced quorum margin increases
the risk of a full outage if another node fails.

**Likely Root Causes**

- A node remains in the Joining state (1) and can't complete SST.
- A node completed SST but hasn't finished catching up (state 3,
  Joined) for an extended period.
- Network partitioning prevents the node from rejoining the cluster.
- Corrupted Galera cache or write-set replication failure.

**Diagnostic and Remediation Steps**

1. Check the current ``wsrep_local_state`` on the affected node:

   .. code-block:: console

     kubectl -n openstack exec -it percona-xtradb-pxc-0 -- \
       mysql -e "SHOW STATUS LIKE 'wsrep_local_state%';"

2. Check overall cluster status:

   .. code-block:: console

     kubectl -n openstack exec -it percona-xtradb-pxc-0 -- \
       mysql -e "SHOW STATUS LIKE 'wsrep_cluster%';"

3. Review the PXC pod logs for the affected replica:

   .. code-block:: console

     kubectl -n openstack logs percona-xtradb-pxc-<N> --tail=200

4. If the node remains in Joining state, it may need an SST restart.
   Delete the affected pod to trigger a fresh SST:

   .. code-block:: console

     kubectl -n openstack delete pod percona-xtradb-pxc-<N>

5. Verify that no PXC backup runs at the moment (a backup puts a node
   into Donor state, which the ``MySQLGaleraDonorFallingBehind`` alert covers):

   .. code-block:: console

     kubectl -n openstack get pxc-backup

``NodeDiskHighLatency``
=======================

This alert fires when the average IO latency on a disk device exceeds 20ms for
at least 1 hour. It measures the time the kernel spends servicing reads and
writes divided by the number of completed operations, which represents the
true per-operation latency at the block device layer.

**Likely root causes:**

- Failing or degraded SSD or HDD (wear-out, bad sectors, firmware issues)
- RAID array running in degraded mode after a disk failure
- Storage controller problems
- Severely overloaded storage subsystem (too many concurrent IO operations)
- Incorrect IO scheduler for the workload type

**Diagnostic and remediation steps:**

1. Identify the affected host and device from the alert labels (``instance``
   and ``device``).

2. Check the current IO latency and throughput on the affected device:

   .. code-block:: console

      iostat -xz 1 5

3. Check for disk errors in the kernel log:

   .. code-block:: console

      dmesg | grep -i -E "error|fault|reset|i/o" | tail -30

4. If the device is part of a RAID array, check the array status:

   .. code-block:: console

      cat /proc/mdstat

5. Check the SMART health status of the underlying drives:

   .. code-block:: console

      smartctl -a /dev/<device>

6. Review whether the host is under unusual IO load:

   .. code-block:: console

      iotop -aoP

7. If the disk shows degradation or failure, plan a replacement. For RAID arrays,
   replace the failed member. For standalone disks, migrate workloads before
   the disk fails completely.

``NodeMemoryHighUtilization``
=============================

This alert fires when computed node memory utilization exceeds 90% for at
least 15 minutes. The calculation uses normal available memory
(``node_memory_MemAvailable_bytes``) plus free huge page capacity
(``node_memory_HugePages_Free * node_memory_Hugepagesize_bytes``), then compares
it with total memory. If huge page metrics are absent on a node, the alert
automatically falls back to ``MemAvailable``-only behavior. This avoids false
positives on compute nodes that intentionally reserve large huge page pools for
VM workloads while preserving normal behavior elsewhere.

**Likely Root Causes**

- Real host-level memory pressure from application or system processes.
- Workload density increase that reduced both normal free memory and free huge
  pages.
- Memory leak in host services, virtualization daemons, or VM workloads.
- Unexpected huge page consumption reducing the free huge page pool.

**Diagnostic and Remediation Steps**

1. Identify the affected node from the alert ``instance`` label.

2. Validate memory pressure from Prometheus metrics:

   .. code-block:: console

      kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
        promtool query instant http://localhost:9090 \
        '(1 - ((node_memory_MemAvailable_bytes{instance="<instance>",job="node-exporter"} + (node_memory_HugePages_Free{instance="<instance>",job="node-exporter"} * node_memory_Hugepagesize_bytes{instance="<instance>",job="node-exporter"})) / node_memory_MemTotal_bytes{instance="<instance>",job="node-exporter"})) * 100'

3. Inspect current host memory and huge page usage:

   .. code-block:: console

      free -h
      grep -E 'HugePages_(Total|Free|Rsvd|Surp)|Hugepagesize' /proc/meminfo

4. Identify the top memory consumers on the host:

   .. code-block:: console

      ps aux --sort=-rss | head -20

5. If huge page usage depletes the free pool, investigate VM placement and
   compute scheduling changes. If normal memory runs out, move workloads,
   increase host capacity, or resolve memory leaks.

``NginxIngressCriticalErrorBudgetBurn``
=======================================

This alert fires when a service behind NGINX Ingress consumes its 30-day error
budget at more than 14.4x the sustainable rate, based on a 99.9% availability
SLO. It uses multi-window burn-rate detection with 1-hour and 5-minute windows
to confirm the issue is both sustained and ongoing. At this burn rate, the
entire 30-day error budget exhausts in under 2.1 days. A minimum traffic guard
of 1 request per second prevents false positives on low-traffic services.

**Likely Root Causes**

- Service pods are crashing or in a crash loop
- Database connection failures affecting all service replicas
- Configuration errors in the service deployment
- Resource exhaustion (CPU, memory, or file descriptors) on service pods
- Network connectivity failures between NGINX and service pods
- Service code bugs causing widespread failures

**Diagnostic and Remediation Steps**

1. Check the alert labels to identify the affected service and query the
   current error rate:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[1h])) / sum by (service) (rate(nginx_ingress_controller_requests[1h]))'

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

``NginxIngressHighErrorBudgetBurn``
====================================

This alert fires when a service behind NGINX Ingress consumes its 30-day error
budget at more than 6x the sustainable rate, based on a 99.9% availability SLO.
It uses multi-window burn-rate detection with 6-hour and 30-minute windows to
confirm the issue is both sustained and ongoing. At this burn rate, the entire
30-day error budget exhausts in under 5 days. A minimum traffic guard of
1 request per second prevents false positives on low-traffic services.

**Likely Root Causes**

- Intermittent issues with a subset of service replicas
- Occasional database query timeouts or connection pool exhaustion
- Resource pressure on some service pods
- Networking issues affecting specific nodes or pods
- Recent deployment causing partial service degradation
- Cache or session storage issues

**Diagnostic and Remediation Steps**

1. Check the current error rate by service:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[6h])) / sum by (service) (rate(nginx_ingress_controller_requests[6h]))'

2. Identify which specific HTTP error codes the service returns:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service, status) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[30m]))'

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

``NginxIngressLowErrorBudgetBurn``
===================================

This alert fires when a service behind NGINX Ingress consumes its 30-day error
budget at the sustainable rate or faster, based on a 99.9% availability SLO. It
uses multi-window burn-rate detection with 3-day and 6-hour windows to confirm
the issue is both sustained and ongoing. At this burn rate, the 30-day error
budget exhausts before the window resets. A minimum traffic guard of 1 request
per second prevents false positives on low-traffic services.

**Likely Root Causes**

- Degrading dependency (database, cache, or external service)
- Gradual resource leak causing occasional failures
- Configuration drift across replicas
- Intermittent infrastructure issues during off-peak hours
- Elevated baseline error rate after a deployment

**Diagnostic and Remediation Steps**

1. Check the error rate trend over the last 3 days:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[3d])) / sum by (service) (rate(nginx_ingress_controller_requests[3d]))'

2. Compare the error rate with the previous period to identify when it started
   increasing by examining trends in Grafana dashboards.

3. Review recent deployments or configuration changes that correlate with the
   error rate increase:

   .. code-block:: console

     kubectl get events -n <namespace> --sort-by='.lastTimestamp' | head -50

4. Check if specific error codes dominate:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service, status) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[6h]))'

5. Investigate resource usage and dependency health for the affected service.

``NginxIngressModerateErrorBudgetBurn``
========================================

This alert fires when a service behind NGINX Ingress consumes its 30-day error
budget at more than 3x the sustainable rate, based on a 99.9% availability SLO.
It uses multi-window burn-rate detection with 1-day and 2-hour windows to
confirm the issue is both sustained and ongoing. At this burn rate, the entire
30-day error budget exhausts in under 10 days. A minimum traffic guard of
1 request per second prevents false positives on low-traffic services.

**Likely Root Causes**

- A subset of service replicas returning errors intermittently
- Slow database queries causing periodic timeouts
- Resource contention during peak traffic periods
- Partial deployment with a faulty version still in rotation
- Upstream dependency experiencing intermittent issues

**Diagnostic and Remediation Steps**

1. Check the error rate over the last day:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[1d])) / sum by (service) (rate(nginx_ingress_controller_requests[1d]))'

2. Identify which error codes the service returns:

   .. code-block:: console

     kubectl -n monitoring exec svc/kube-prometheus-stack-prometheus -- \
       promtool query instant http://localhost:9090 \
       'sum by (service, status) (rate(nginx_ingress_controller_requests{status=~"5[0-9]{2}"}[2h]))'

3. Check for unhealthy pods or recent restarts:

   .. code-block:: console

     kubectl get pods -A | grep <service-name>
     kubectl get events -n <namespace> --sort-by='.lastTimestamp' | grep <service-name>

4. Review application logs for recurring errors:

   .. code-block:: console

     kubectl logs -n <namespace> -l app=<service-name> --tail=200 | grep -i error

5. Check if errors correlate with traffic patterns or specific time windows in
   Grafana.

6. Review recent deployments or configuration changes that might have
   introduced the issue.

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


``SmartctlDiskAttributeFailing``
=================================

This alert fires when a SMART attribute's normalized value drops at or
below the per-attribute failure threshold the drive firmware itself
defines (``smartctl_device_attribute{attribute_value_type="value"}`` is
``<=`` the matching ``thresh``, where ``thresh > 0``). The drive itself
declares one of its prefailure attributes has crossed into the failing
zone. Common cases are end-of-life wear indicators on SATA SSDs and
reallocation or pending-sector counters whose normalized values have
decayed below the firmware threshold. Suppressed when
``SmartctlDiskUnhealthy`` already fires for the same disk.

**Likely Root Causes**

- SATA SSD wear-out (vendor wearout indicator below threshold)
- Sustained reallocation pressure dropping the normalized
  ``Reallocated_Sector_Ct`` value
- Any vendor-specific prefailure attribute the drive deems failing

**Diagnostic and Remediation Steps**

1. Identify the affected disk and attribute from the alert labels
   (``instance``, ``device``, ``attribute_id``, ``attribute_name``).

2. Inspect all SMART attributes and note any flagged ``FAILING_NOW``:

   .. code-block:: console

     smartctl -A /dev/<device>

3. Cross-check with ``SmartctlDiskUnhealthy``: if both fire, the
   overall SMART status is also failing. Replace the drive immediately.

4. If only this alert fires, the drive is still functional but the
   firmware predicts the attribute will continue to degrade. Plan
   replacement during the next maintenance window.

``SmartctlDiskAvailableSpareLow``
==================================

This alert fires when an NVMe drive's ``available_spare`` percentage drops
below the manufacturer-defined ``available_spare_threshold``. NVMe drives
maintain a pool of spare blocks for media defects. Once that pool nears
exhaustion the controller marks the drive at risk of imminent failure.

**Likely Root Causes**

- The drive is at end-of-life from sustained writes
- The drive has experienced an unusually high number of bad blocks
- Firmware degradation tracking the drive itself classifies as critical

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Review the spare and threshold values:

   .. code-block:: console

     smartctl -a /dev/<device> | grep -iE 'available_spare'

3. Cross-check the NVMe ``critical_warning`` field, which the controller
   sets in parallel:

   .. code-block:: console

     smartctl -a /dev/<device> | grep -i 'critical warning'

4. Migrate any data off the disk and order an emergency replacement. Don't
   wait for the next maintenance window.

``SmartctlDiskCriticalWarning``
================================

This alert fires when an NVMe drive's ``critical_warning`` bitfield is
non-zero. The controller sets bits to indicate available spare below
threshold, temperature over critical, NVM subsystem reliability degraded,
media in read-only mode, or volatile-memory backup failed. Any non-zero
value is the manufacturer's own signal that the drive is unsafe.

**Likely Root Causes**

- Available spare exhausted (bit 0)
- Temperature exceeded the drive's own critical threshold (bit 1)
- NVM subsystem reliability degraded (bit 2)
- Media in read-only mode (bit 3)
- Volatile-memory backup device failed (bit 4)

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Decode the active bit:

   .. code-block:: console

     smartctl -a /dev/<device> | grep -iA1 'critical warning'

3. Address the underlying cause: cooling for temperature, replacement for
   reliability/media-read-only/spare-exhausted.

4. Migrate data and replace the drive. Treat any non-zero
   ``critical_warning`` as an imminent-failure signal.

``SmartctlDiskMediaErrorsGrowing``
===================================

This alert fires when an NVMe drive's ``media_errors`` counter increased
over the last 24 hours. The counter records occurrences where the
controller couldn't recover data via ECC. A stable non-zero count from
historical events is harmless, but ongoing growth means the media is
actively degrading.

**Likely Root Causes**

- Media wear at end-of-life
- A bad NAND die or controller bug
- Sustained high temperatures damaging cells

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Confirm the current count and trend:

   .. code-block:: console

     smartctl -a /dev/<device> | grep -i 'media.*errors'

3. Compare with ``smartctl_device_percentage_used`` to decide whether
   wear-out or a localized fault is the cause.

4. Schedule replacement during the next maintenance window. If the rate
   of growth is high, escalate to immediate replacement.

``SmartctlDiskPendingSectorsGrowing``
======================================

This alert fires when a SATA drive's ``Current_Pending_Sector`` (attribute
197) grew over the last 24 hours. A stable non-zero count is harmless.
The drive remaps those sectors on the next write attempt. Ongoing
growth indicates active media degradation: the drive is encountering new
sectors it can't read or write reliably.

**Likely Root Causes**

- Physical wear on platters or NAND cells
- Mechanical shock or vibration
- Read disturb errors on busy SSD blocks

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Check the current pending count and other reallocation attributes:

   .. code-block:: console

     smartctl -A /dev/<device> | grep -iE 'pending|reallocated|uncorrectable'

3. Run a long self-test to force reallocation attempts:

   .. code-block:: console

     smartctl -t long /dev/<device>

4. Re-check after the test completes (typically a few hours). If pending
   sectors continue to grow, schedule replacement.

``SmartctlDiskReallocatedSectorsGrowing``
==========================================

This alert fires when a SATA drive's ``Reallocated_Sector_Ct`` (attribute
5) grew over the last 24 hours. A stable non-zero value (for example,
factory remapping) is harmless, but ongoing growth means the drive is
actively remapping new bad sectors.

**Likely Root Causes**

- Physical wear or age-related degradation
- Mechanical shock or vibration
- Overheating causing intermittent write failures

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Check the current count and trend:

   .. code-block:: console

     smartctl -A /dev/<device> | grep -iE 'reallocated|pending'

3. Plan replacement during the next maintenance window. If the count is
   accelerating, escalate to an unplanned replacement.

``SmartctlDiskScsiGrownDefectsGrowing``
========================================

This alert fires when a SCSI/SAS drive's grown defect list
(``smartctl_scsi_grown_defect_list``) gains entries over the last 24
hours. A stable non-zero count is harmless. Ongoing growth means the
drive is actively reallocating bad blocks. This alert is the SAS analog
of ``SmartctlDiskReallocatedSectorsGrowing``.

**Likely Root Causes**

- Mechanical wear on SAS HDD platters
- Vibration or shock damage
- Approaching end of rated life

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Review the defect list and SMART attributes:

   .. code-block:: console

     smartctl -a /dev/<device>

3. Plan replacement during the next maintenance window. Escalate if
   growth is accelerating or if ``SmartctlDiskScsiUncorrectedErrors``
   also fires for the same drive.

``SmartctlDiskScsiUncorrectedErrors``
======================================

This alert fires when a SCSI/SAS drive's read or write
total-uncorrected-error counter
(``smartctl_read_total_uncorrected_errors`` /
``smartctl_write_total_uncorrected_errors``) increases over the last 24
hours. Any non-zero growth means the drive couldn't recover I/O via
on-disk ECC, confirming data loss in the affected blocks.

**Likely Root Causes**

- Severe media degradation
- Mechanical or electronics fault
- SAS bus errors hammering the drive

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Inspect the SCSI error counter log and overall health:

   .. code-block:: console

     smartctl -l error /dev/<device>
     smartctl -a /dev/<device>

3. Migrate any data off the disk and replace it. Don't return the drive
   to service.

``SmartctlDiskSelfTestFailed``
===============================

This alert fires when a SATA drive reports one or more entries in its
SMART self-test error log. Even one failed self-test indicates the
drive couldn't complete an internal integrity check. The upstream
``smartctl_exporter`` only emits this metric for ATA/SATA drives. NVMe
self-test results aren't surfaced.

**Likely Root Causes**

- Bad sectors detected during the self-test
- Mechanical or electronics fault
- Drive firmware or controller errors

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Review the self-test log:

   .. code-block:: console

     smartctl -l selftest /dev/<device>

3. Run a fresh self-test to confirm the failure:

   .. code-block:: console

     smartctl -t long /dev/<device>

4. If failures persist, plan replacement during the next maintenance
   window.

``SmartctlDiskTemperatureHigh``
================================

This alert fires when a disk's current temperature exceeds 65°C sustained
for at least one hour. Brief spikes during heavy I/O are normal,
especially on NVMe drives, but sustained high temperatures accelerate
flash memory wear and can cause data loss or mechanical failure.

**Likely Root Causes**

- Inadequate server cooling or airflow around the disk bay
- Failed or degraded cooling fans
- High ambient temperature in the data center
- Sustained heavy workload with insufficient cooling

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Check current and historical temperatures:

   .. code-block:: console

     smartctl -a /dev/<device> | grep -i temperature

3. Check the server's fan speeds via IPMI:

   .. code-block:: console

     ipmitool sdr type Fan

4. Inspect airflow paths for obstruction. Verify that the disk bay isn't
   blocked.

5. If ambient temperature has risen, escalate to facilities.

``SmartctlDiskUncorrectableSectorsGrowing``
============================================

This alert fires when a SATA drive's ``Offline_Uncorrectable`` (attribute
198) grew over the last 24 hours. A stable non-zero count is harmless
because those sectors represent already-acknowledged bad blocks. Ongoing
growth means the drive is finding new sectors it can't recover during
background scans, indicating confirmed unrecoverable data loss in newly
affected LBAs.

**Likely Root Causes**

- Physical damage to platters
- Severe NAND wear
- Mechanical shock

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Determine which files (if any) live on the affected sectors:

   .. code-block:: console

     smartctl -a /dev/<device>

3. Check filesystem integrity (offline if necessary):

   .. code-block:: console

     fsck -nv /dev/<device>

4. Migrate any data off the disk and replace it. Don't return the drive
   to service.

``SmartctlDiskUnhealthy``
==========================

This alert fires when a disk fails its SMART overall-health
self-assessment (``smartctl_device_smart_status == 0``). The drive
firmware predicts imminent failure. Replace the disk immediately to
prevent data loss.

**Likely Root Causes**

- The disk has exceeded its rated endurance
- Reallocated, pending, or uncorrectable sector counts crossed the
  manufacturer's critical threshold
- Catastrophic hardware failure or firmware corruption

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Verify SMART health and review all attributes:

   .. code-block:: console

     smartctl -H /dev/<device>
     smartctl -a /dev/<device>

3. Migrate data immediately to a healthy replica. Don't defer.

4. Order an emergency replacement; don't wait for a maintenance window.

``SmartctlDiskWearoutCritical``
================================

This alert fires when an NVMe drive reports more than 90% of its rated
endurance used (``smartctl_device_percentage_used > 90``) sustained for
at least 15 minutes. At this wear level the manufacturer considers
near-term failure likely. ``SmartctlDiskAttributeFailing`` covers SATA
drives instead, since they expose wear via vendor-specific normalized
attributes rather than ``percentage_used``.

**Likely Root Causes**

- The disk has been in heavy write workloads for an extended period
- A workload exceeded the disk's rated endurance (write amplification)
- The disk is approaching end of its rated lifetime

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Confirm the wear level:

   .. code-block:: console

     smartctl -a /dev/<device> | grep -i percentage_used

3. Review workload sizing. If the workload exceeded the disk's rated
   endurance, plan a higher-endurance class for the replacement.

4. Order a replacement. Schedule replacement during the next maintenance
   window, sooner if ``SmartctlDiskUnhealthy`` also fires.

``SmartctlDiskWearoutWarning``
================================

This alert fires when an NVMe drive reports more than 75% of its rated
endurance used (``smartctl_device_percentage_used > 75``) sustained for
at least one hour. The drive still operates within specification but is
approaching end of life. Suppressed automatically when
``SmartctlDiskWearoutCritical`` fires for the same disk.
``SmartctlDiskAttributeFailing`` covers SATA drives instead.

**Likely Root Causes**

- The disk has been in heavy write workloads for an extended period
- A workload exceeded the disk's rated endurance (write amplification)

**Diagnostic and Remediation Steps**

1. Identify the affected disk from the alert labels (``instance`` and
   ``device``).

2. Check the wear trend in Grafana or Prometheus to estimate time to
   failure.

3. Plan a replacement during the next scheduled maintenance window.
