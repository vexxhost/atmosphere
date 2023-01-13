# Custom Registry

You can use your own local registry to store the Atmosphere images.  The scope
of this document does not include how to setup a local registry.

1. Mirror all images to your own registry

   ```bash
   atmosphere image mirror 192.168.0.20:5000/atmosphere
   ```

2. Update the Atmosphere image repository variable

   ```yaml
   atmosphere_image_repository: 192.168.0.20:5000/atmosphere
   ```

3. If needed, you can also set your registry to be an insecure registry inside
   `containerd`:

   ```yaml
    containerd_insecure_registries:
      - 192.168.0.20:5000/atmosphere
    ```

4. You can verify that all your images are running from your local registry by
   running the following command:

   ```bash
   kubectl get pods --all-namespaces \
      -o jsonpath="{.items[*].spec.containers[*].image}" | \
         tr -s '[[:space:]]' '\n' | \
         sort | \
         uniq -c | \
         sort -n
   ```
