import yaml
from pbr.version import VersionInfo

GALAXY_YML = {
    'namespace': 'vexxhost',
    'name': 'atmosphere',
    'version': VersionInfo('ansible-collection-atmosphere').release_string().replace('.dev', '-'),
    'readme': 'README.md',
    'authors': [
        "Mohammed Naser <mnaser@vexxhost.com>",
    ],
    'dependencies': {
        'ansible.posix': '1.3.0',
        'ansible.utils': '2.5.2',
        'community.crypto': '2.2.3',
        'community.general': '4.5.0',
        'kubernetes.core': '2.3.2',
        'openstack.cloud': '1.7.0',
    },
    'build_ignore': [
        '.tox',
        '.vscode',
        'doc',
    ],
}

with open('galaxy.yml', 'w') as f:
    yaml.dump(GALAXY_YML, f, default_flow_style=False)
