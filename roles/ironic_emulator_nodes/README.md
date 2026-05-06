# `ironic_emulator_nodes`

Stands up two libvirt-backed emulated bare-metal nodes (`node-0`,
`node-1`) on the AIO host so that Ironic, Nova
(`nova-compute-ironic`), and Magnum/CAPI can be exercised end-to-end
without real hardware.

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `bm_emulator_gpu_enabled` | `false` | Attach a virtio-gpu device to each emulated BM VM, register a `CUSTOM_GPU` trait on each Ironic node, and create a `baremetal-gpu` Nova flavor that requires the trait. Used to test GPU "passthrough" all the way to a pod on a Magnum/CAPI Kubernetes cluster. |

## Prerequisite: kube image preparation

Before creating any Magnum cluster against these emulated BM nodes, the
Kubernetes image you upload to Glance MUST be prepared for two
constraints baked into this AIO:

### 1. Image must be RAW (not qcow2) — gap #14

Atmosphere's AIO uses Ceph RBD as the Glance/Cinder backend. Ceph RBD
requires the source image to be in **raw** format; if you upload the
upstream `ubuntu-2204-kube-vX.Y.Z` qcow2 directly, Glance accepts it
but Nova/Ironic spawn fails when copying it onto the BM node.

Convert qcow2 → raw before upload:

```bash
# Download the upstream image
wget https://object-storage.public.mtl1.vexxhost.net/swift/v1/.../\
ubuntu-2204-kube-v1.34.3.qcow2

# Convert to raw on the AIO host
qemu-img convert -f qcow2 -O raw \
    ubuntu-2204-kube-v1.34.3.qcow2 \
    ubuntu-2204-kube-v1.34.3.raw

# Upload as raw to Glance
openstack image create ubuntu-2204-kube-v1.34.3-raw \
    --disk-format raw --container-format bare \
    --file ubuntu-2204-kube-v1.34.3.raw \
    --property os_distro=ubuntu --property os_version=22.04
```

Then reference `ubuntu-2204-kube-v1.34.3-raw` (not the qcow2 name) in
`coe cluster template create --image …`.

> Permanent fix would be to add a `roles/glance_images` task that
> uploads the raw form by default. Until that lands, do the conversion
> by hand on the AIO host before cluster create.

### 2. Strip `nomodeset` from the image's GRUB cmdline — gap #20

The upstream `ubuntu-2204-kube-vX.Y.Z` cloud images (at least up to
v1.34.3) bake the following into `GRUB_CMDLINE_LINUX_DEFAULT`:

```
nomodeset nofb gfxpayload=text
```

`nomodeset` tells the kernel to refuse loading any KMS GPU driver. On
a BM VM with a virtio-gpu attached (i.e. `bm_emulator_gpu_enabled:
true`), this means:

- `virtio_gpu` probe fails with `error -22` (visible in `dmesg`).
- `/dev/dri/card0` is **never** created.
- The fake-GPU device-plugin advertises `vexxhost.com/fake-gpu = 0` on
  the node, so workloads requesting the GPU resource sit Pending
  forever.

There are two ways to fix it:

**a) Image-side (preferred, persistent across reboots and rebuilds)**

Strip the tokens out of `/etc/default/grub` *inside the image* before
uploading, e.g. via `virt-customize`:

```bash
virt-customize -a ubuntu-2204-kube-v1.34.3.raw \
  --run-command "sed -i 's/ nomodeset//g; s/ nofb//g; s/ gfxpayload=text//g' \
                  /etc/default/grub && update-grub"
```

Then upload the modified raw image to Glance.

**b) Per-node workaround (one-shot, after the BM node is already up)**

If you only realise after `coe cluster create` that the worker has no
GPU device, fix it on the booted node and reboot it once:

```bash
# From the AIO host (or any pod with kubectl + privileges), run:
sed -i 's/ nomodeset//g; s/ nofb//g; s/ gfxpayload=text//g' \
    /etc/default/grub
update-grub
reboot
```

After the node comes back, delete the fake-GPU device-plugin pod on
that node so kubelet re-enumerates devices:

```bash
kubectl -n kube-system delete pod \
  -l app.kubernetes.io/name=fake-gpu-device-plugin \
  --field-selector spec.nodeName=<worker-node-name>
```

`vexxhost.com/fake-gpu` should flip from `0` to `1` and the demo pod
will schedule.

> Permanent fix is to either rebuild the kube image with the cleaned
> cmdline (option a) or add a Magnum cluster cloud-init `runcmd` that
> strips the tokens before the post-bootstrap reboot. Both are
> out-of-tree relative to atmosphere.

## End-to-end fake-GPU passthrough — full walkthrough

This section is the canonical step-by-step procedure to take a freshly
deployed AIO (with `bm_emulator_gpu_enabled: true`) all the way to a
running pod that consumes `vexxhost.com/fake-gpu` and sees a real
`/dev/dri/cardN` device.

When `bm_emulator_gpu_enabled: true` is set, the role:

1. Adds `<video><model type='virtio'/></video>` to each libvirt domain
   so the BM VM sees a Virtio GPU PCI device (`/dev/dri/cardN` inside).
2. Tags each Ironic node with the `CUSTOM_GPU` trait.
3. Creates an additional `baremetal-gpu` Nova flavor with
   `trait:CUSTOM_GPU=required`.

The walkthrough below assumes you've already run the AIO deploy and
have shell on the AIO host as `root` with `OS_CLOUD=system` available.

### Phase 0 — Preflight (do these BEFORE `coe cluster create`)

These steps avoid the gaps documented earlier in this README. Do them
in order. Skipping any of them will leave the cluster in a broken
state that is hard to recover from later.

**0.1. Confirm the AIO base is healthy.**

```bash
kubectl -n openstack get pods | grep -E 'ironic|nova|magnum'
openstack baremetal driver list                       # redfish must appear
openstack hypervisor list                             # ironic hypervisor present
```

**0.2. Confirm both BM nodes are enrolled and `available` (gap #13).**

```bash
openstack baremetal node list
# expect:
#   node-0  available  power off
#   node-1  available  power off
```

If the list is empty or partial, the `Prepare Ironic virtual nodes`
task (now idempotent and fail-loud — gap #13 fix on this branch)
either errored out or hasn't been re-run. Re-run the role with the
`ironic-emulator` tag, or fall back to the manual `enroll_node` recipe
in `~/notes/logs/ironic/mcapi-bm/commands.md` §5.

**0.3. Confirm libvirt domains use KVM + host-passthrough (gaps #18, #19).**

```bash
kubectl -n openstack exec -it -c libvirt \
  $(kubectl -n openstack get pod -l application=libvirt -o name | head -1) \
  -- virsh dumpxml --inactive node-0 | head -20
# expect:  <domain type='kvm'>  and  <cpu mode='host-passthrough'/>
```

If you see `type='qemu'` or `mode='host-model'`, the role pre-dates
the `bm-mcapi-fixes` patches — re-run the role or apply the live
recipes in `~/notes/logs/ironic/mcapi-bm/commands.md` §2.

**0.4. Prepare the kube image (gaps #14 and #20).**

See "Prerequisite: kube image preparation" above. In short:

```bash
# (gap #14) Convert qcow2 → raw
qemu-img convert -f qcow2 -O raw \
    ubuntu-2204-kube-v1.34.3.qcow2 ubuntu-2204-kube-v1.34.3.raw

# (gap #20) Strip nomodeset before upload
virt-customize -a ubuntu-2204-kube-v1.34.3.raw \
  --run-command "sed -i 's/ nomodeset//g; s/ nofb//g; s/ gfxpayload=text//g' \
                  /etc/default/grub && update-grub"

# Upload as raw
openstack image create ubuntu-2204-kube-v1.34.3-raw \
    --disk-format raw --container-format bare \
    --file ubuntu-2204-kube-v1.34.3.raw \
    --property os_distro=ubuntu --property os_version=22.04
```

**0.5. Create the network + keypair the cluster will use.**

```bash
# External network 'public' should already exist from the AIO deploy.
openstack network show public >/dev/null

# Cluster needs a keypair so the master VM is reachable for any
# manual recovery (see Phase 3 troubleshooting).
ssh-keygen -t ed25519 -N '' -f /root/.ssh/bmkey -C bmkey
openstack keypair create --public-key /root/.ssh/bmkey.pub bmkey
```

### Phase 1 — Create the BM Magnum cluster

**IMPORTANT — flavor choice (gap #15):**
- `--master-flavor` MUST be a baremetal flavor (e.g. `baremetal`) so
  the control plane lands on an Ironic node, NOT on the AIO host as a
  Nova KVM VM. If you omit `--master-flavor` Magnum will pick the Heat
  default (typically `m1.small`/`m1.large`), which silently puts
  kube-apiserver on a VM and the cluster will *appear* to work but
  the emulation isn't end-to-end BM.
- `--flavor` (worker) is `baremetal-gpu` so the GPU trait is consumed
  where the workload pods land. With only 2 emulated BM nodes this
  gives 1 BM master + 1 BM-GPU worker, which fits exactly.
- If you want the master on GPU too, use `baremetal-gpu` for both and
  bump `bm_emulator_node_count` (or add a 3rd node manually).

**IMPORTANT — `boot_volume_size` and `server_type=bm` (gap #17):**
the AIO ironic-conductor is deployed with `storage_interface=noop`,
not wired to Cinder, so volume-backed boot fails at spawn time with
`Missing parameters: ['instance_info.image_source']`. The cluster
template MUST end up with `boot_volume_size=0` so Magnum boots the
BM node directly from the Glance image (which is what `noop`
supports).

- **mcapi `add-server-type-bm` branch (commit `e61ca8d`) and newer:**
  if the cluster_template has `server_type=bm` and the operator does
  NOT pass `boot_volume_size` explicitly, mcapi auto-defaults it to
  `0`. You can omit the label.
- **older mcapi:** you MUST pass `--labels boot_volume_size=0`
  explicitly, otherwise the chart renders a Cinder root volume
  request that Ironic refuses.

The example below passes `boot_volume_size=0` explicitly so it works
on both old and new mcapi.

```bash
# 1.1 — Cluster template
openstack coe cluster template create k8s-bm-gpu \
    --image ubuntu-2204-kube-v1.34.3-raw \
    --flavor baremetal-gpu --master-flavor baremetal \
    --external-network public --network-driver calico \
    --keypair bmkey \
    --coe kubernetes --docker-storage-driver overlay2 \
    --labels kube_tag=v1.34.3,boot_volume_size=0,octavia_provider=ovn

# 1.2 — Cluster (1 BM master + 1 BM-GPU worker)
openstack coe cluster create gpu-test \
    --cluster-template k8s-bm-gpu \
    --master-count 1 --node-count 1

# 1.3 — Watch progress
watch -n 10 'openstack coe cluster show gpu-test \
    -f value -c status -c health_status; \
    openstack baremetal node list'
```

Expected sequence:
- both Ironic nodes go `available → deploying → wait call-back → active`
- master Nova instance becomes `ACTIVE` first, then worker
- `coe cluster show` reaches `CREATE_COMPLETE` / `HEALTHY`
- typical end-to-end time on this AIO: 12–18 minutes

If the cluster is stuck in `CREATE_IN_PROGRESS` for more than ~25
minutes, jump to "Phase 3 — Troubleshooting" below.

**Verify both nodes really landed on BM (gap #15 sanity check):**

```bash
for srv in $(openstack server list -f value -c ID); do
  openstack server show "$srv" -f value -c name -c flavor
done
# both should show flavor=baremetal or baremetal-gpu
# if any shows m1.* the master/worker is on a Nova VM, NOT BM.
```

### Phase 2 — Validate the GPU passthrough

**2.1. Get the workload kubeconfig.**

```bash
openstack coe cluster config gpu-test --dir /tmp/gpu-test --force
export KUBECONFIG=/tmp/gpu-test/config

kubectl get nodes -o wide
# expect: 1 master (control-plane) + 1 worker, both Ready, v1.34.x
```

**2.2. Apply the fake-GPU device plugin.**

```bash
kubectl apply -f roles/ironic_emulator_nodes/files/fake-gpu-device-plugin.yaml

# wait for the DaemonSet to be Running on every node
kubectl -n kube-system get pods \
  -l app.kubernetes.io/name=fake-gpu-device-plugin -o wide
```

**2.3. Confirm the GPU resource is advertised on the worker.**

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: \
fake-gpu={.status.allocatable.vexxhost\.com/fake-gpu}{"\n"}{end}'

# expect:
#   <master-node>:fake-gpu=0
#   <worker-node>:fake-gpu=1
```

If the worker shows `fake-gpu=0`, you almost certainly skipped step
0.4 (gap #20). On the worker:

```bash
ls /dev/dri/                # /dev/dri/card0 must exist
dmesg | grep -i virtio_gpu  # must NOT show "probe failed with error -22"
```

If `/dev/dri` is empty, apply the in-node `nomodeset` workaround from
the prerequisites section, reboot the node, and then:

```bash
kubectl -n kube-system delete pod \
  -l app.kubernetes.io/name=fake-gpu-device-plugin \
  --field-selector spec.nodeName=<worker-node-name>
```

so kubelet re-enumerates devices.

**2.4. Run the demo pod.**

```bash
kubectl apply -f roles/ironic_emulator_nodes/files/fake-gpu-demo-pod.yaml

# wait for the pod to start (it will sleep 600s after probing)
kubectl get pod fake-gpu-demo -o wide
kubectl logs fake-gpu-demo
```

The demo pod's logs will show:

- `lspci` output containing `VGA compatible controller: Red Hat, Inc.
  Virtio 1.0 GPU` — the virtio-gpu PCI device this role attached to
  the libvirt domain.
- `/dev/dri/card0` listed under `/dev/dri` — the device file kubelet
  injected via the device-plugin contract.
- `vexxhost.com/fake-gpu` accounted in the pod's resource request, so
  the fact that it Scheduled at all proves the resource was advertised
  and consumed end-to-end.

`kubectl describe node <worker>` should show `vexxhost.com/fake-gpu`
under both `Capacity` and `Allocatable`, and `1` under `Allocated
resources` while `fake-gpu-demo` is Running.

### Phase 3 — Health checks (self-serve)

Quick sanity script you can rerun any time:

```bash
echo "== cluster ==";    openstack coe cluster show gpu-test \
    -f value -c status -c health_status
echo "== BM nodes ==";   openstack baremetal node list
echo "== nova ==";       openstack server list --long \
    -f value -c Name -c Status -c Flavor -c Networks
echo "== k8s nodes =="; KUBECONFIG=/tmp/gpu-test/config \
    kubectl get nodes -o wide
echo "== readyz ==";    KUBECONFIG=/tmp/gpu-test/config \
    kubectl get --raw='/readyz?verbose' | tail -5
echo "== gpu ==";       KUBECONFIG=/tmp/gpu-test/config \
    kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: \
fake-gpu={.status.allocatable.vexxhost\.com/fake-gpu}{"\n"}{end}'
echo "== demo ==";      KUBECONFIG=/tmp/gpu-test/config \
    kubectl get pod fake-gpu-demo -o wide
```

Healthy output:
- cluster `CREATE_COMPLETE` / `HEALTHY`
- both BM nodes `active`, both Nova servers `ACTIVE` with BM flavors
- both k8s nodes `Ready`
- `readyz check passed`
- worker advertises `fake-gpu=1`
- `fake-gpu-demo` `Running` (or `Completed` if 10 min after start)

### Phase 4 — Teardown / re-test

```bash
openstack coe cluster delete gpu-test
# wait until DELETE_COMPLETE, then nodes flip back to available
openstack baremetal node list
```

The `enroll_node` task is idempotent (gap #13 fix), so you can repeat
Phases 1–3 without re-running the whole role.

If you need to fully re-prepare the libvirt domains (e.g. you're
testing the role itself), `virsh destroy node-0 node-1; virsh undefine
node-0 node-1; ironic-emulator-nodes` re-creates them; then resume at
Phase 0.

### Troubleshooting matrix

| Symptom | Most likely gap | Fix |
| --- | --- | --- |
| `coe cluster create` fails `NoValidDriver` | #2 | install mcapi from `add-server-type-bm` branch |
| Cluster stuck `CREATE_IN_PROGRESS`, `Missing parameters: ['instance_info.image_source']` in nova-compute logs | #17 | upgrade mcapi to `add-server-type-bm` branch (auto-defaults to `0` for `server_type=bm`), OR recreate cluster template with `--labels boot_volume_size=0,...` |
| Cluster stuck `CREATE_IN_PROGRESS`, BM node stays `wait call-back`, libvirt VM has died | #18 | confirm `<domain type='kvm'>` (Phase 0.3) |
| BM node deploys, then crashes on second power cycle with `guest CPU doesn't match specification` | #19 | confirm `<cpu mode='host-passthrough'/>` (Phase 0.3) |
| `kubeadm init` hangs, kube-apiserver crashloops on master | #3 | run "Master VM recovery" procedure below |
| KCP stays `WaitingForKubeadmInit` forever after fixing apiserver | #5 | run "Master VM recovery" procedure below |
| Pods scheduled but kubelet refuses extra ones with "no allocatable …" | #4 | bump `maxPods: 250` on the kubelet config and restart kubelet |
| Worker Ready but `fake-gpu=0` | #20 | strip `nomodeset` from `/etc/default/grub`, reboot, recycle plugin pod |
| `coe cluster create` fails because nodes never went `available` | #13 | `openstack baremetal node list`; rerun the `Prepare Ironic virtual nodes` task or `commands.md §5` |
| BM node fails to bind VIF with "not enough free physical ports" | #16 | confirm `network_interface=flat` on the node (now default in this branch) |

### Master VM recovery — gaps #3 and #5

Symptoms (any one is enough to suspect this):

- `openstack coe cluster show gpu-test` sits in `CREATE_IN_PROGRESS`
  for >15 min after the master VM is `ACTIVE`.
- On the management AIO: `kubectl -n magnum-system get
  kubeadmcontrolplane -A` shows `INITIALIZED=false` and
  `Conditions[*].Reason=WaitingForKubeadmInit`.
- SSH to the master, `sudo crictl ps -a | grep apiserver` shows
  `kube-apiserver` restarting every ~10s.
- `sudo crictl logs <apiserver-id>` contains `unable to load
  configuration from "…/keystone-auth/webhook.kubeconfig": no such
  file or directory`.

This means cloud-init hit gap #3 (kube-apiserver crashloops on
missing k8s-keystone-auth webhook config), kubeadm aborted, and gap
#5 means kubeadm doesn't auto-resume on its own.

**Recovery procedure (run on the master VM as root):**

```bash
# From the AIO host:
ssh -i /root/.ssh/bmkey ubuntu@<master-fip>
sudo -i

# 1. Strip the webhook flags from the static apiserver manifest.
#    Kubelet auto-restarts the static pod when this file changes.
sed -i \
  -e '/--authentication-token-webhook-config-file/d' \
  -e '/--authorization-webhook-config-file/d' \
  -e 's/--authorization-mode=Node,RBAC,Webhook/--authorization-mode=Node,RBAC/' \
  /etc/kubernetes/manifests/kube-apiserver.yaml

# 2. Wait for kube-apiserver to come up clean.
until crictl ps | grep -q kube-apiserver; do sleep 5; done
KUBECONFIG=/etc/kubernetes/admin.conf kubectl get --raw='/healthz'
# expect: ok

# 3. Run the kubeadm finalize phases that cloud-init never reached.
#    /run/kubeadm/kubeadm.yaml is preserved by cloud-init.
export KUBECONFIG=/etc/kubernetes/admin.conf
kubeadm init phase upload-config kubeadm   --config /run/kubeadm/kubeadm.yaml
kubeadm init phase upload-config kubelet   --config /run/kubeadm/kubeadm.yaml
kubeadm init phase bootstrap-token         --config /run/kubeadm/kubeadm.yaml
kubeadm init phase mark-control-plane      --config /run/kubeadm/kubeadm.yaml
kubeadm init phase kubelet-finalize all    --config /run/kubeadm/kubeadm.yaml
kubeadm init phase addon all               --config /run/kubeadm/kubeadm.yaml

# 4. Sanity check on the workload cluster
kubectl get nodes                                  # master should show Ready
kubectl -n kube-system get pods                    # kube-proxy + coredns Running
```

Back on the management AIO, KCP flips to `Initialized=true` within a
minute, CAPI starts bootstrapping the worker, and the cluster reaches
`CREATE_COMPLETE` shortly after.

**Note on Keystone authn:** stripping the webhook flags disables
Keystone-backed authn/authz on the cluster. For the fake-GPU demo
this is fine (we use the cluster-admin kubeconfig from
`coe cluster config`). If you actually need Keystone authn, deploy
`k8s-keystone-auth` Helm chart (`magnum-cluster-api` chart `cloud-provider-openstack/k8s-keystone-auth`)
manually after the cluster is up, then re-add the two flags to
`/etc/kubernetes/manifests/kube-apiserver.yaml`.

**Permanent fixes (out-of-tree, in mcapi cloud-init template):**

- Gap #3: pre-stage `k8s-keystone-auth` as a static pod manifest
  written by cloud-init **before** `kubeadm init` runs, so the
  webhook endpoints exist when kube-apiserver starts.
- Gap #5: wrap `kubeadm init` in a retry loop that detects partial
  state and re-runs only the missing phases, OR ship a one-shot
  `kubeadm-finalize.service` that runs the missing phases on every
  boot until they succeed and then disables itself.


## Known gaps (not yet automated in this branch)

The following fixes were applied **manually** during the live debug
session that produced this branch but are **not** yet baked into the
deployment. A clean redeploy with this branch will still require some
of these workarounds until they land.

1. **`vexxhost.ceph` loopback-guard.** The Galaxy collection task
   `Fail if there is any existing loopback devices` in
   `create_fake_devices.yml` aborts the AIO build if any leftover
   loopback devices exist (e.g. from a prior failed run). Lives in the
   external `vexxhost.ceph` collection, not this repo. Workaround:
   strip the task on the host before re-running. See the atmosphere
   skill's "Deployment Debugging" section.
2. **mcapi BM driver.** Upstream `magnum-cluster-api` advertises only
   `server_type=vm`. To land BM clusters we currently set the
   cluster-template flavor to `baremetal` so Nova routes via
   `nova-compute-ironic`. A proper fix that adds `server_type=bm` to
   each driver's `provides()` is staged on branch
   [`add-server-type-bm`](https://github.com/vexxhost/magnum-cluster-api/tree/add-server-type-bm)
   in `vexxhost/magnum-cluster-api` (commit `a73063a`). Until it
   merges, install mcapi from that branch when redeploying this AIO,
   e.g.:

   ```bash
   pip install \
       git+https://github.com/vexxhost/magnum-cluster-api@add-server-type-bm
   ```
3. **k8s-keystone-auth chicken-and-egg.** Magnum cluster cloud-init
   wires `--authentication-token-webhook-config-file` and
   `--authorization-webhook-config-file` into the kube-apiserver
   manifest before `k8s-keystone-auth` is deployed, so the apiserver
   crashloops and `kubeadm init` never reaches `upload-config`. Live
   workaround: strip the webhook flags from
   `/etc/kubernetes/manifests/kube-apiserver.yaml` and run the
   `kubeadm init phase upload-config|bootstrap-token|mark-control-plane|kubelet-finalize`
   phases by hand. Proper fix: pre-deploy `k8s-keystone-auth` as a
   static pod via cloud-init so the webhook endpoints exist before the
   apiserver starts.
4. **Kubelet `maxPods=250` for AIO-BM.** The host kubelet defaults
   (110) cap pod density on the AIO controller when running BM
   workloads + Magnum control plane + system pods. Bump
   `maxPods: 250` in the kubeadm/kubelet config template applied
   during the AIO bootstrap.
5. **Idempotent kubeadm finalize.** When cloud-init's `kubeadm init`
   crashes mid-bootstrap (typically due to gap #3), it never retries
   the finalize phases on its own. Make the cloud-init template detect
   partial state and re-run the missing phases automatically so the
   master comes up clean without operator intervention.
6. **Cinder-backed boot for BM nodes (`storage_interface=cinder`).**
   The Magnum default cluster template used to request Cinder
   volume-backed boot (`boot_volume_size > 0`) regardless of
   `server_type`, but this role's ironic-conductor is deployed with
   `storage_interface=noop` and not wired to Cinder, so volume boot
   failed at Nova spawn with `Missing parameters:
   ['instance_info.image_source']`.

   - **Upstream fix landed** in `vexxhost/magnum-cluster-api`
     `add-server-type-bm` branch (commit `e61ca8d`): when
     `server_type=bm` and the operator does not pass
     `boot_volume_size` explicitly, mcapi auto-defaults it to `0`.
     Operators on this branch can drop the label.
   - **Operator workaround for older mcapi** (and what this README's
     example uses for compatibility): pass
     `--labels boot_volume_size=0,...` so Magnum boots the BM node
     directly from the Glance image.
   - **Longer-term proper fix:** enable
     `enabled_storage_interfaces=cinder,noop` on ironic-conductor,
     set `--storage-interface cinder` per BM node, and attach Cinder
     volume targets — then `boot_volume_size>0` would actually work.
7. **Kube image must be RAW for Ceph RBD backend.** The atmosphere AIO
   uses Ceph RBD as the Glance/Cinder backend, which requires `raw`
   source images. The upstream `ubuntu-2204-kube-vX.Y.Z` cloud images
   ship as qcow2; uploading them as-is causes Nova/Ironic spawn to
   fail. Operator workaround: convert `qemu-img convert -f qcow2 -O
   raw …` and upload the raw form — see "Prerequisite: kube image
   preparation" §1 above. Proper fix: add a `roles/glance_images` task
   that uploads the raw form by default.
8. **Upstream kube image bakes `nomodeset` into GRUB.** The upstream
   `ubuntu-2204-kube-vX.Y.Z` cloud images set
   `GRUB_CMDLINE_LINUX_DEFAULT=… nomodeset nofb gfxpayload=text …`,
   which prevents `virtio_gpu` from probing on emulated BM nodes
   (`/dev/dri/cardN` never appears) and the fake-GPU device-plugin
   advertises `0`. Operator workaround: strip the tokens out of the
   image before upload (`virt-customize` recipe in §2 above) or, if
   already booted, edit `/etc/default/grub` on the node + `update-grub`
   + reboot. Proper fix: rebuild the kube image with the cleaned
   cmdline, OR add a Magnum cluster cloud-init `runcmd` that strips
   the tokens before the post-bootstrap reboot.
