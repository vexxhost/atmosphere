#!/usr/bin/python3

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        who=dict(type='str', required=True),
        name=dict(type='str', required=True),
        value=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    who = module.params['who']
    name = module.params['name']
    value = module.params['value']

    changed = False

    _, out, _ = module.run_command(
        ['ceph', 'config', 'get', who, name], check_rc=True
    )

    if out.strip() != value:
        changed = True

    if not module.check_mode:
        _, _, _ = module.run_command(
            ['ceph', 'config', 'set', who, name, value], check_rc=True
        )

    module.exit_json(changed=changed)


def main():
    run_module()


if __name__ == '__main__':
    main()