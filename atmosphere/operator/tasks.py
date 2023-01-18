import glob
import os
import subprocess

import pkg_resources
from taskflow import task

from atmosphere.operator import constants, utils


class InstallClusterApiTask(task.Task):
    def execute(self, spec: dict):
        cluster_api_images = [
            i for i in constants.IMAGE_LIST if i.startswith("cluster_api")
        ]

        # TODO(mnaser): Move CAPI and CAPO to run on control plane
        manifests_path = pkg_resources.resource_filename(__name__, "manifests")
        manifest_files = glob.glob(os.path.join(manifests_path, "capi-*.yml"))

        for manifest in manifest_files:
            with open(manifest) as fd:
                data = fd.read()

            # NOTE(mnaser): Replace all the images for Cluster API
            for image in cluster_api_images:
                data = data.replace(
                    utils.get_image_ref(image).string(),
                    utils.get_image_ref(
                        image, override_registry=spec["imageRepository"]
                    ).string(),
                )

            subprocess.run(
                "kubectl apply -f -",
                shell=True,
                check=True,
                input=data,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
