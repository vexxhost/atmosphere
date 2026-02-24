---
name: zuul
description: Troubleshoot failing Zuul CI jobs for this project. Use this when asked to debug, investigate, or fix Zuul job failures.
---

# Zuul CI troubleshooting

## Finding the Zuul check for a PR

Get the list of checks for the pull request. Identify the Zuul check by
looking for a check whose URL points to a Zuul instance (typically
containing `/buildset/` in the path). Note the check name, status, and
buildset URL for further investigation.

## Getting buildset details via Zuul API

Zuul's dashboard is an SPA so you cannot scrape it directly. Use the
REST API instead. Extract the Zuul base URL and buildset UUID from the
check URL, then call:

    GET <zuul_base_url>/api/buildset/<buildset_uuid>

The response is JSON containing the buildset result, pipeline, refs, and
a `builds` array. Each build has `job_name`, `result`, `duration`,
`log_url`, and `error_detail`. Use this to identify which specific
job(s) failed within the buildset.

## Log retrieval

For details on reading job logs, scanning the artifact manifest, and
the artifact directory structure, see `.github/skills/zuul/logs.md`.

## Troubleshooting approach

1. Start with the buildset API to identify which job(s) failed.
2. Grep `job-output.txt` for `FAILED` (excluding `RETRYING`) and
   `PLAY RECAP` with `failed=` > 0 to locate the failure point.
3. If the failure is in a verify/test stage (for example tempest), check
   whether the converge stage itself passed (`failed=0`) — the root
   cause may be environmental rather than a deployment error.
4. Use the scan-manifest script to discover available artifacts, then
   inspect host-level state (networking, routes, processes) and pod
   logs for the relevant services.
5. Cross-reference Ansible task output (`ok` vs `changed` vs `failed`)
   with the actual system state from artifacts — tasks can report
   success while the underlying command silently fails.

## Comparing variants in the same buildset

When a buildset has multiple job variants (for example OVN vs OVS, or
different CSI backends), and only one variant fails:

1. Check whether the same test passed in the other variant — this
   narrows the root cause to what differs between them (networking
   backend, storage driver, node configuration).
2. Compare system-level artifacts (routes, interfaces, bridge config)
   between the passing and failing jobs to spot environmental
   differences.
3. A failure in only one variant often points to an infrastructure or
   configuration issue rather than a code bug.

## Analyzing tempest failures

Tempest is the OpenStack integration test suite used in the verify
stage. When tempest tests fail:

1. Use the scan-manifest script to find the tempest pod logs (search
   for "tempest"). The `tempest-run-tests` pod log contains the full
   tempest output and is much easier to parse than searching through
   `job-output.txt`.
2. Categorize the failure type:
   - **SSH/connectivity timeouts**: Likely a networking or routing issue
     on the test host. Check interface state, routes, and bridge config.
   - **API errors (4xx/5xx)**: Check the pod logs for the failing
     OpenStack service (for example Neutron, Nova, Cinder).
   - **Resource creation failures**: Check quota, scheduling, and the
     relevant service logs.
3. Use the scan-manifest script to find pod logs for the service under
   test and look for errors or crashes around the timestamp of the
   failure.
4. When a test fails with a timeout waiting for a resource, trace
   through the chain: check the service worker logs first, then the
   compute logs (Nova) to verify the underlying VM state, then the
   host networking artifacts (routes, interfaces). A resource stuck in
   a pending state often means the control plane cannot reach the data
   plane — verify connectivity, not just that the VM exists.

## Analyzing service failures

When OpenStack or infrastructure services are unhealthy:

1. Use the scan-manifest script to search for the service name and find
   its pod logs and Kubernetes object descriptions.
2. Check for pods in `failed-pods/` — these are pods that were not
   running at the time of log collection.
3. Review Helm release status in the helm artifacts to see if the
   deployment itself succeeded.
4. Check the Kubernetes object descriptions for events, restart counts,
   and readiness probe failures.

## Analyzing Ansible failures

When Ansible tasks fail or behave unexpectedly:

1. Look for `PLAY RECAP` lines to identify which play had failures.
2. Search backward from the recap to find the specific `TASK` that
   failed and its error output.
3. Watch for tasks that use `|| true`, `ignore_errors`, or
   `failed_when: false` — these mask real errors. A task can show `ok`
   in the recap but have actually failed underneath.
4. Check whether plays that run privileged commands have `become: true`.
   If a molecule scenario or Zuul job changed how privilege escalation
   is configured (for example removing a global `ansible_become`
   setting), individual plays may need explicit `become: true`.
5. Verify variable values by checking the generated workspace config
   and Ansible facts in the job output.
