#####################
Selective Molecule CI
#####################

Atmosphere uses a declarative impact policy to avoid deploying every service
for every pull request. The policy maps changed paths to the smallest safe
Molecule scenario, deployment dependency closure, and verification profile.
Unknown runtime paths deliberately fall back to the complete test suite.

The implementation is independent from deployment orchestration. Zuul jobs
inherit the ordinary Atmosphere Molecule jobs and execute the same sequential
Ansible playbooks used by ``main``. For a selective AIO job, the planner passes
the dependency closure as native Ansible tags to the normal converge and
idempotence actions.

Policy
======

The policy is stored in ``ci/molecule-plan.yaml`` and has three sections:

``jobs``
  Static Zuul jobs which can consume a decision.

``rules``
  Shared paths, ignored paths, focused scenario paths, and conservative
  full-suite fallbacks.

``components``
  Role and chart ownership, direct CI dependencies, verification profiles, and
  the jobs which exercise each component. A component can also declare
  ``tempest_tests`` regular expressions to restrict Tempest to its smoke tests.

Dependencies describe the test environment, not deployment concurrency. For
example, a Keystone change includes Kubernetes, Ceph-backed CSI, the Percona
XtraDB Cluster, Keycloak, RabbitMQ, Memcached, ingress, and certificate
components. It does not include Glance, Nova, Manila, Magnum, or other unrelated
OpenStack APIs.

Changing the policy
===================

Add or update a component in ``ci/molecule-plan.yaml`` when introducing a role
or chart. Keep dependencies explicit and prefer the narrowest job which performs
meaningful verification. Shared code should use a ``full`` rule unless its
impact is safely bounded.

Validate the policy and inspect representative plans locally:

.. code-block:: console

   uv run python -m atmosphere.ci.molecule_plan validate
   uv run python -m atmosphere.ci.molecule_plan plan \
     --changed-file roles/glance/tasks/main.yml
   uv run python -m atmosphere.ci.molecule_plan plan \
     --changed-file roles/neutron/tasks/main.yml

The planner evaluates both sides of renames and copies. Documentation and
release-note-only changes produce a no-op plan. A path which matches no rule or
component produces a full plan so a new runtime area cannot silently lose test
coverage.

In Zuul, the planner compares the speculative merge commit at ``HEAD`` with its
first parent at ``HEAD^1``. For an ordinary pull request, the first parent is
the target branch. For a pull request with ``Depends-On`` changes, it also
contains those dependencies, so only the current pull request selects test
targets.

During selective AIO verification, Tempest receives the union of
``tempest_tests`` for the changed components. The expressions are passed
through Tempest's ``include-list`` support and combined with ``--smoke``. A
component without expressions, including any such component in a multi-target
change, uses the ordinary smoke selection against the services available in
its deployment closure. This provides a conservative fallback for services
whose image has no dedicated smoke-test namespace.

Zuul artifacts
==============

Every scheduled selective job prints its decision and publishes
``ci-plan-<job>.json`` with the job logs. Running Molecule output is polled and
printed throughout the deployment. Progress heartbeats report the last
observed Molecule task, while the complete stream is retained as
``molecule-<job>.log``.

Zuul constructs the job graph before a project job can inspect the pull request
diff, so all five consumer jobs are scheduled statically. Jobs which are not
selected report ``SKIP`` and exit without running Molecule, but still require a
node for their inherited preparation. Avoiding that allocation would require
moving change classification into trusted Zuul configuration.

The selective AIO jobs allow fifteen minutes for Keycloak and ten minutes for
the Nova, Neutron, and Octavia Helm operations. Clean database migrations and
initial service rollouts can exceed their normal timeouts on a busy test node
even when they complete successfully. The complete AIO Molecule lifecycle has
a 150-minute command limit so full fallback runs have enough time to finish
idempotence and verification.
