==================================
OVN Logging Solution Documentation
==================================

********
Overview
********
This document outlines the architecture, configuration, and usage of the OVN
logging solution for capturing, enriching, and forwarding security group logs
to Loki. The solution uses dual sidecars per OVN Controller Pod, enabling
efficient log processing and enrichment while maintaining compatibility with
the Atmosphere project.

************
Architecture
************

Components
==========

1. **Vector Sidecar**: Captures and processes OVN security group logs from a
   shared volume.
2. **HTTP Sidecar**: Enriches logs with OpenStack `project_id` and `domain_id``
   and forwards them to Loki.

Log Flow
========

1. OVN Controller generates security group logs and writes them to a shared
   volume (or hostPath). [1]
2. The Vector sidecar reads logs from the shared volume, applies basic parsing,
   and forwards them to the HTTP sidecar.
3. The HTTP sidecar enriches the logs with project_id and domain_id based on
   the Neutron database and forwards them back to Vector. [2]
4. Vector sends the enriched logs to Loki.

Diagram
=======

::

   OVN Logs => Shared Volume => Vector Sidecar => HTTP Sidecar (Enrichment) => Vector => Loki

*************
Configuration
*************

Vector Sidecar Configuration
============================

You can override vector configuration via OVN Helm values.
For example, you can use Openstack `domain_id` as Loki `tenant_id`` instead of
using Openstack `project_id` by using this values.

.. note::

    You'll need to use `{% raw %} ... {% endraw %}` for Helm templating `{{ }}`
    because Jinja2 templating in Ansible conflicts with Helm templating.

.. code-block:: yaml

  ovn_helm_values:
    conf:
      vector: |
        [sources.file_logs]
        type = "file"
        include = [ "/logs/ovn-controller.log" ]

        [sinks.ovn_log_parser_in]
        type = "http"
        inputs = ["file_logs"]
        uri = "{% raw %}{{ tuple "ovn_logging_parser" "default" "api" . | include "helm-toolkit.endpoints.keystone_endpoint_uri_lookup" }}{% endraw %}"
        encoding.codec = "json"
        method = "post"

        [sources.ovn_log_parser_out]
        type = "http_server"
        address = "0.0.0.0:5001"
        encoding = "json"

        [transforms.parse_log_message]
        type = "remap"
        inputs = ["ovn_log_parser_out"]
        source = '''
          del(.source_type)
          del(.path)
        '''

        [sinks.loki_sink]
        type = "loki"
        labels.event_source = "network_logs"
        inputs = ["parse_log_message"]
        endpoint = "http://loki.monitoring:3100"
        encoding.codec = "json"
        tenant_id = "{% raw %}{{`{{ domain_id }}`}}{% endraw %}"


*****
Usage
*****

You can check logs in Grafana UI. In explorer page, you can set a label filter
`event_source=network_logs` which has been configured in vector loki sink
configuration.

   .. image:: images/ovn_logging_result.png
      :alt: Description of the image
      :width: 600
      :align: center


*********
Reference
*********

1. https://docs.openstack.org/neutron/latest/admin/config-logging.html
2. https://github.com/vexxhost/neutron-ovn-network-logging-parser
