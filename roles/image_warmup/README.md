# `image_warmup`

This role pre-pulls every container image listed in `_atmosphere_images`
on every Kubernetes node using `crictl`. Running it once the cluster is
ready ensures that subsequent component Helm installs schedule pods
whose images are already cached, removing most `ImagePulling` waits
from the deploy critical path.

Pulls run with bounded concurrency and any failure is logged but
non-fatal so that on-demand pulls can still satisfy missing images
later.
