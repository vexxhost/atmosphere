from django.conf import settings
from django.utils.translation import ugettext_lazy as _

# Service group names (global across all projects):
MONITORING_SERVICES_GROUPS = [
    {'name': _('OpenStack Services'), 'groupBy': 'service'},
    {'name': _('Servers'), 'groupBy': 'hostname'}
]

# Services being monitored
MONITORING_SERVICES = getattr(
    settings,
    'MONITORING_SERVICES_GROUPS',
    MONITORING_SERVICES_GROUPS
)

MONITORING_SERVICE_VERSION = getattr(
    settings, 'MONITORING_SERVICE_VERSION', '2_0'
)
MONITORING_SERVICE_TYPE = getattr(
    settings, 'MONITORING_SERVICE_TYPE', 'monitoring'
)
MONITORING_ENDPOINT_TYPE = getattr(
    # NOTE(trebskit) # will default to OPENSTACK_ENDPOINT_TYPE
    settings, 'MONITORING_ENDPOINT_TYPE', None
)

# Grafana button titles/file names (global across all projects):
# GRAFANA_LINKS = [{"raw": True, "path": "monasca-dashboard", "title": "Sub page1"}]
GRAFANA_LINKS = []
DASHBOARDS = getattr(settings, 'GRAFANA_LINKS', GRAFANA_LINKS)

GRAFANA_URL = {"regionOne": "/grafana"}

SHOW_GRAFANA_HOME = getattr(settings, 'SHOW_GRAFANA_HOME', True)

ENABLE_LOG_MANAGEMENT_BUTTON = getattr(
    settings, 'ENABLE_LOG_MANAGEMENT_BUTTON', False)
ENABLE_EVENT_MANAGEMENT_BUTTON = getattr(
    settings, 'ENABLE_EVENT_MANAGEMENT_BUTTON', False)

KIBANA_POLICY_RULE = getattr(settings, 'KIBANA_POLICY_RULE',
                             'monitoring:kibana_access')
KIBANA_POLICY_SCOPE = getattr(settings, 'KIBANA_POLICY_SCOPE',
                              'monitoring')
KIBANA_HOST = getattr(settings, 'KIBANA_HOST',
                      'http://192.168.10.6:5601/')

OPENSTACK_SSL_NO_VERIFY = getattr(
    settings, 'OPENSTACK_SSL_NO_VERIFY', False)
OPENSTACK_SSL_CACERT = getattr(
    settings, 'OPENSTACK_SSL_CACERT', None)

POLICY_FILES = getattr(settings, 'POLICY_FILES', {})
POLICY_FILES.update({'monitoring': 'monitoring_policy.json', })  # noqa
setattr(settings, 'POLICY_FILES', POLICY_FILES)
