# `ironic_emulator_nodes`

Stands up two libvirt-backed emulated bare-metal nodes (`node-0`,
`node-1`) on the AIO host so that Ironic, Nova
(`nova-compute-ironic`), and Magnum/CAPI can be exercised end-to-end
without real hardware.

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `bm_emulator_gpu_enabled` | `false` | Attach a virtio-gpu device to each emulated BM VM, register a `CUSTOM_GPU` trait on each Ironic node, and create a `baremetal-gpu` Nova flavor that requires the trait. Used to test GPU "passthrough" all the way to a pod on a Magnum/CAPI Kubernetes cluster. |

## End-to-end fake-GPU passthrough

When `bm_emulator_gpu_enabled: true` is set, the role:

1. Adds `<video><model type='virtio'/></video>` to each libvirt domain
   so the BM VM sees a Virtio GPU PCI device (`/dev/dri/cardN` inside).
2. Tags the corresponding Ironic node with the `CUSTOM_GPU` trait.
3. Creates an additional `baremetal-gpu` Nova flavor with
   `trait:CUSTOM_GPU=required`.

To verify the chain is wired up correctly, after the deployment
finishes:

```bash
# 1. Create a Magnum cluster pinned to the GPU-flavored BM nodes.
openstack coe cluster template create k8s-bm-gpu \
    --image ubuntu-2204-kube-v1.34.3 \
    --flavor baremetal-gpu --master-flavor baremetal-gpu \
    --external-network public --network-driver calico \
    --keypair bmkey \
    --coe kubernetes --docker-storage-driver overlay2 \
    --labels kube_tag=v1.34.3,boot_volume_size=0
openstack coe cluster create gpu-test --cluster-template k8s-bm-gpu \
    --master-count 1 --node-count 1
openstack coe cluster config gpu-test --dir /tmp/gpu-test
export KUBECONFIG=/tmp/gpu-test/config

# 2. Apply the fake GPU device plugin to the workload cluster.
kubectl apply -f roles/ironic_emulator_nodes/files/fake-gpu-device-plugin.yaml

# 3. Wait for the resource to appear on the worker.
kubectl get nodes -o json | \
    jq '.items[].status.allocatable["vexxhost.com/fake-gpu"]'

# 4. Run the demo pod and inspect the device passthrough.
kubectl apply -f roles/ironic_emulator_nodes/files/fake-gpu-demo-pod.yaml
kubectl logs fake-gpu-demo
```

The demo pod's logs will show the Virtio GPU PCI device via `lspci`,
the `/dev/dri/cardN` device file injected by kubelet, and confirm the
pod was scheduled because of the requested `vexxhost.com/fake-gpu`
extended resource.

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
2. **mcapi BM driver.** `magnum-cluster-api` advertises only
   `server_type=vm`. To land BM clusters we currently set the
   cluster-template flavor to `baremetal` so Nova routes via
   `nova-compute-ironic`. A proper fix is to add `server_type=bm` in
   the mcapi driver's `provides()` (external repo
   `vexxhost/magnum-cluster-api`).
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
